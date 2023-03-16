<script lang="ts">
    import { onMount } from "svelte";

    import { image } from "../camdata";

    let canvas;
    let min;
    let max;
    let range;

    // $: console.log($image);
    onMount(() => {
        let ctx: CanvasRenderingContext2D = canvas.getContext("2d");
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "low";

        ctx.fillStyle = "#202124";
        ctx.fillRect(0, 0, 32, 24);
    });

    image.subscribe((img) => {
        if (!img) return;

        min = img[0];
        max = img[0];

        for (const [i, t] of img.entries()) {
            min = Math.min(min, t);
            max = Math.max(max, t);
        }

        let range = max - min | 1;
        console.log(range);
        let ctx: CanvasRenderingContext2D = canvas.getContext("2d");
        for (let row = 0; row < 24; row++) {
            for (let col = 0; col < 32; col++) {
                let idx = 32 * row + 31 - col;
                let px = img[idx];
                if (idx == -1) {
                    ctx.fillStyle = `red`;
                } else {
                    ctx.fillStyle = `rgb(
                    ${Math.floor((255 * (px - min)) / range)},
                    ${Math.floor((255 * (px - min)) / range)},
                    ${Math.floor((255 * (px - min)) / range)})`;
                }

                ctx.fillRect(col, row, 1, 1);
            }
        }
    });
</script>

<div>
    <canvas bind:this={canvas} width="32" height="24" />
    <p>min:{min} max:{max} range:{range}</p>
</div>

<style>
    canvas {
        padding: 1rem;
        box-sizing: border-box;
        min-width: 0;
        min-height: 0;
        width: 100%;
        height: 100%;
        image-rendering: pixelated;
        aspect-ratio: 32/24;
        object-fit: contain;
    }
    div {
        height: 100%;
        overflow: hidden;
    }
</style>
