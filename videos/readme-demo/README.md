# README demo video

The source of the demo GIF at the top of the project README, made with
[HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP, rendered to video).
Every piece of text on screen comes from real output: the samples in `samples/inputs/` and `samples/outputs/`
(PDF, scan, Word, slides, web page, image, e-book and email),
the NIST IR 8425 diagram description and the 78-page scan of the Statistical Abstract of the United States 1920 (U.S. Census Bureau, public domain)
from the evaluation.

- `BRIEF.md` and `STORYBOARD.md`: what the video says, scene by scene.
- `index.html` mounts the scenes in `compositions/`; `assets/` holds the page images.

Re-render from the repository root with Docker (no AI calls):

```bash
docker build -t everymd-demo-render:0.8.121 videos/readme-demo
docker run --rm --shm-size=512m -v "$PWD/videos/readme-demo:/project" everymd-demo-render:0.8.121 hyperframes check
docker run --rm --shm-size=512m -v "$PWD/videos/readme-demo:/project" everymd-demo-render:0.8.121 hyperframes render --fps 30 --quality delivery -o renders/everymd-demo.mp4
docker run --rm -v "$PWD/videos/readme-demo:/project" -v "$PWD/docs/assets:/out" everymd-demo-render:0.8.121 ffmpeg -y -i renders/everymd-demo.mp4 -vf "fps=12,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" -loop 0 /out/everymd-demo.gif
```
