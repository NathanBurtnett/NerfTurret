<script lang="ts">
  import { onMount } from "svelte";
  import CamControls from "./lib/CamControls.svelte";
  import Camviewer from "./lib/Camviewer.svelte";
  import Greet from "./lib/Greet.svelte";
</script>

<main>
  <h1>MLX Viewer</h1>

  <Camviewer />
  <CamControls />
  <p>Made by Dominic C. for ME405</p>
</main>

<style>
  :global(html) {
    height: 100%;
    width: 100%;
    margin: 0;
    padding: 0;
  }

  :global(body) {
    height: 100%;
    width: 100%;
    margin: 0;
    padding: 0;
  }

  main {
    display: grid;
    grid-template-columns: auto 20rem;
    grid-template-rows: auto 1fr auto;
    column-gap: 3rem;
    height: 100%;
    padding: 0.5rem 0.5rem;
    box-sizing: border-box;
  }

  h1 {
    grid-column: 1 / 3;
    display: block;
    background-color: slategray;
    margin: 0 0 1rem 0;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 1px 1px 10px #000;
  }
  p {
    margin: 0;
  }
</style>
