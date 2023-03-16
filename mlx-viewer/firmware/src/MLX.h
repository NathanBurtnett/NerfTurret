#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_MLX90640.h>
#define IMG_WIDTH 32
#define IMG_HEIGHT 24
#define IMG_PIXELS IMG_HEIGHT *IMG_WIDTH
#define ADDR 0x33

/**
 * Viewer protocol:
 * Total packet format is <0xFE><CMD><LEN><LEN><DATA>
 */

struct CamInfo
{
    bool en_subpage_mode;
    bool en_data_hold;
    bool en_subpage_repeat;
    uint8_t select_subpage;
    uint8_t refresh_rate;
    uint8_t resolution;
    uint8_t pattern;
} __attribute__((packed));

class MLX
{
public:
    const short ADDR_STATUS = 0x8000;
    const short ADDR_CR1 = 0x800D;

    float temp_frame[IMG_PIXELS]; // buffer for full frame of temperatures
    uint8_t blob_map[IMG_PIXELS];
    uint16_t raw_frame[834];

    Adafruit_MLX90640 amlx;
    float ta = 0;
    TwoWire &w;

    uint8_t api_buf[255];
    size_t api_len;
    size_t api_idx;
    uint8_t api_cmd;
    enum
    {
        SYNC,
        RX_CMD,
        RX_LEN,
        RX_DAT,
    } api_state;

    struct
    {
        long t_frame_fetch;
        long t_frame_tx_time;
        long t_calc_time;
    } cam_timing;

    struct
    {
        float cx;
        float cy;
    } analysis;

    struct
    {
        float tmin = 26;
        float tamb_min = 100;
        float tmax = 36;
    } tuning __attribute__((packed));

    union
    {
        struct
        {
            unsigned en_subpage_mode : 1;
            unsigned : 1;
            unsigned en_data_hold : 1;
            unsigned en_subpage_repeat : 1;
            unsigned select_subpage : 3;
            unsigned refresh_rate : 3;
            unsigned resolution : 2;
            unsigned use_chessboard_pattern : 1;
        } cr1;
        uint16_t cr1_word;
    };

    MLX(TwoWire &wire) : w(wire)
    {
    }

    void write_cam_params()
    {
        amlx.MLX90640_I2CWrite(ADDR, ADDR_CR1, cr1_word);
    }

    void read_cam_params()
    {
        amlx.MLX90640_I2CRead(ADDR, ADDR_CR1, 1, &cr1_word);
    }

    bool init()
    {
        delay(80);
        tx_debug("Initializing MLX90640!");
        int status = 0;

        amlx.begin(ADDR, &Wire);
        cr1.en_subpage_mode = 1;
        cr1.en_data_hold = 0;
        cr1.en_subpage_repeat = 0;
        cr1.refresh_rate = 5;
        cr1.resolution = 2;
        cr1.use_chessboard_pattern = 0;

        write_cam_params();
        read_cam_params();

        tx_debug("Initialized!");
        return true;
    }

    bool has_img()
    {
        return false;
    }

    long read_img()
    {

        float emissivity = 0.95;
        int status;

        long t = millis();
        status = amlx.MLX90640_GetFrameData(0, raw_frame);
        cam_timing.t_frame_fetch = millis() - t;

        if (status < 0)
        {
            return status;
        }

        ta = amlx.MLX90640_GetTa(raw_frame, &amlx._params) - OPENAIR_TA_SHIFT; // For a MLX90640 in the open air the shift is -8

        t = millis();
        amlx.MLX90640_CalculateTo(raw_frame, &amlx._params, emissivity, ta, temp_frame);
        cam_timing.t_calc_time = millis() - t;

        return 0;
    }

    void tx_current_image()
    {
        long t = millis();
        tx(0x00, &temp_frame);
        cam_timing.t_frame_tx_time = millis() - t;
    }

    void tx_debug(const char *msg)
    {
        tx(0x01, msg, strlen(msg));
    }

    void tx_debugf(const char *fmt, ...)
    {
        char msg[255];

        va_list args;
        va_start(args, fmt);
        tx(0x01, msg, vsnprintf(msg, 255, fmt, args));
        va_end(args);
    }

    void tx_current_params()
    {
        // CamInfo c{
        //     cr1.en_subpage_mode,
        //     cr1.en_data_hold,
        //     cr1.en_subpage_repeat,
        //     static_cast<uint8_t>(cr1.select_subpage),
        //     static_cast<uint8_t>(cr1.refresh_rate),
        //     static_cast<uint8_t>(cr1.resolution),
        //     static_cast<uint8_t>(cr1.use_chessboard_pattern),
        // };

        // tx(0x02, &c);
    }

    void preprocess()
    {
        float temp_min = tuning.tmin;
        float temp_max = tuning.tmax;

        float amax = -100.;

        // Linear Threshold
        // for (size_t i; i < IMG_PIXELS; i++)
        // {
        //     if (temp_frame[i] > temp_max || temp_frame[i] < temp_min)
        //     {
        //         temp_frame[i] = temp_min;
        //     }

        //     amax = max(temp_frame[i], amax);
        // }

        // Binary mask
        for (size_t i; i < IMG_PIXELS; i++)
        {
            if (temp_frame[i] > temp_max || temp_frame[i] < temp_min)
            {
                temp_frame[i] = 0;
            }
            else
            {
                temp_frame[i] = 1;
            }
        }
    }

    void detect_blobs()
    {
    }
    void detect_centroid()
    {
        float temp_min = tuning.tmin;
        float temp_max = tuning.tmax;
        float range = temp_max - temp_min;

        analysis.cx = 0;
        analysis.cy = 0;

        for (size_t row = 0; row < 24; row++)
        {
            for (size_t col = 0; col < 32; col++)
            {
                float px = temp_frame[row * 32 + col];
                analysis.cx += px * col;
                analysis.cy += px * row;
            }
        }

        analysis.cx /= IMG_PIXELS;
        analysis.cy /= IMG_PIXELS;
    }

    void tx_timings()
    {
        tx(0x03, &cam_timing);
    }

    void tx_analysis()
    {
        tx(0x04, &analysis);
    }

    template <typename T>
    void tx(uint8_t cmd, T *t, uint16_t len = sizeof(T))
    {
        Serial.write(0xA0);
        Serial.write(cmd); // CMD
        Serial.write((uint8_t *)&len, 2);
        Serial.write((uint8_t *)t, len);
    }

    void rx(uint8_t b)
    {
        switch (api_state)
        {
        case SYNC:
            if (b == 0xA0)
                api_state = RX_CMD;
            break;

        case RX_CMD:
            api_cmd = b;

            api_idx = 0;
            api_state = RX_LEN;
            break;

        case RX_LEN:
            ((uint8_t *)&api_len)[api_idx++] = b;
            if (api_idx >= 2)
            {
                if (api_len > 255)
                    api_state = SYNC;
                else
                    api_state = RX_DAT;
                api_idx = 0;
            }
            break;

        case RX_DAT:
            api_buf[api_idx++] = b;

            if (api_idx >= api_len)
            {
                interpret_rx();
                api_state = SYNC;
            }
        }
    }

    void interpret_rx()
    {
        switch (api_cmd)
        {
        case 0x01: // Ingest tuning
            memcpy(&tuning, api_buf, api_len);
            // tx_debugf("Tuning A1 %d", api_buf[3]);
            // tx_debugf("Tuning A2 %d", api_buf[0]);

            tx_debugf("Tuning TMIN %f", tuning.tmin);
            tx_debugf("Tuning TMAX %f", tuning.tmax);
            tx_debugf("Tuning TAMB %f", tuning.tamb_min);

            break;
        }
    }
};
