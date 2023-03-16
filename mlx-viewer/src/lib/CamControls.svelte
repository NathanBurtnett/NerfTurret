<script lang="ts">
    import { onMount } from "svelte";
    import {
        closeSerialPort,
        writeTuning,
        initSerialPort,
        tmax,
        logs,
        timings,
        portOpen,
        tmin,
        tamb_min,
        analysis,
    } from "../camdata";

    let ports = [];
    onMount(() => {
        //document.scrollingElement.scroll(0, 1);
    });
</script>

<div class="control-container">
    {#if !$portOpen}
        <button on:click={initSerialPort}>Open Port</button>
    {:else}
        <button on:click={closeSerialPort} class="connected">Close Port</button>
    {/if}
    <h3>Tuning</h3>
    <div class="inputs">
        <p>tmin</p>
        <input type="number" bind:value={$tmin} />

        <p>Tmax</p>
        <input type="number" bind:value={$tmax} />

        <p>tamb_min</p>
        <input type="number" bind:value={$tamb_min} />
    </div>
    <button on:click={writeTuning}>Save</button>

    {#if $timings}
        <h3>Timings</h3>
        <p>Calc time: {$timings.t_calc_time}</p>
        <p>Frame Fetch: {$timings.t_frame_fetch}</p>
        <p>TX time: {$timings.t_frame_tx_time}</p>
        <h3>Analysis</h3>
        <p>cx: {$analysis.cx}</p>
        <p>cy: {$analysis.cy}</p>
    {/if}
    <h3>Log</h3>
    <div class="logs-scroller">
        <div class="logs">
            {#each $logs as log (log.idx)}
                <pre>{log.idx} - {log.msg}</pre>
            {/each}
        </div>
    </div>
</div>

<style>
    .inputs {
        display: grid;
        grid-template-columns: auto auto;
        gap: 0.5rem;
        justify-items: right;
    }
    label {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .logs {
        color: black;
        overflow-y: visible;
        height: fit-content;
    }

    .logs-scroller {
        background-color: whitesmoke;
        overflow-y: scroll;
        display: flex;
        flex-direction: column-reverse;
        height: 10rem;
    }

    .logs * {
        margin: 0;
    }
    .connected {
        background-color: darkslategray;
    }
</style>
