import streamlit as st

aquarium_component = st.components.v2.component(
    name = "aquarium",
    html = """
        <div id="aquarium-container"></div>
    """,
    css = """
        body {
            margin: 0;
            overflow: hidden;
        }

        .aquarium {
            position: relative;
            width: 100%;
            height: 400px;

            background:
                linear-gradient(
                    to bottom,
                    #a9d8ef,
                    #7bb8df
                );

            overflow: hidden;
        }

        .floor {
            position: absolute;

            bottom: 0;
            left: 0;

            width: 100%;
            height: 60px;

            background:
                linear-gradient(
                    to bottom,
                    #f7edc8,
                    #dfcf9b
                );

            z-index: 1;
        }

        .floor::before {
            content: "";

            position: absolute;

            top: -10px;
            left: 0;

            width: 100%;
            height: 20px;

            background:
                radial-gradient(
                    ellipse,
                    rgba(255,255,255,.35) 0%,
                    transparent 70%
                );

            opacity: .5;
        }

        .fish-container {
            position: absolute;
            left: -30%;

            animation-name: swim;
            animation-timing-function: linear;
            animation-iteration-count: infinite;
            animation-fill-mode: both;

            animation-duration: var(--speed, 20s);
            animation-delay: var(--delay, 0s);

            top: var(--depth, 20%);

            transform: scale(var(--size, 1));

            z-index: 5;
        }

        .bubble {
            position: absolute;

            left: var(--left);
            bottom: 0px;

            width: var(--size);
            height: var(--size);

            border-radius: 50%;

            background: transparent;

            border: 1px solid rgba(255,255,255,.45);

            box-shadow:
                inset 2px 2px 2px rgba(255,255,255,.2);

            animation:
                rise var(--duration) linear infinite;

            animation-delay: var(--delay);

            pointer-events: none;

            z-index: 1;
        }

        .bubble::after {
            content: "";

            position: absolute;

            width: 20%;
            height: 20%;

            top: 20%;
            left: 20%;

            border-radius: 50%;

            background: rgba(255,255,255,.8);

            filter: blur(1px);
        }

        svg {
            width: 130px;
            height: auto;
        }

        .kelp-container {
            position: absolute;
            inset: 0;

            z-index: 2;
        }

        .kelp {
            position: absolute;

            bottom: 10px;
            left: var(--left);

            height: 200px;

            transform: scale(var(--scale));

            transform-origin: bottom center;
        }

        .kelp svg {
            height: 100%;
            width: auto;
        }

        /* animate tail */
        [id$="fish-tail"] {
            transform-box: fill-box;
            transform-origin: left center;

            animation:
                tail-wag
                var(--fin-speed, .7s)
                ease-in-out
                infinite alternate;
        }

        /* animate fin */
        [id$="pectoral-fin"] {
            transform-box: fill-box;
            transform-origin: top center;

            animation:
                fin-flutter
                var(--fin-speed, .7s)
                ease-in-out
                infinite alternate;
        }

        /* animate bubbles */
        @keyframes rise {
            from {
                transform: translate(0, 0);
                opacity: 1;
            }
            to {
                transform: translate(var(--drift), -380px);
                opacity: 1;
            }
        }

        /* animate fish swimming */
        @keyframes swim {
            0% {
                left: -140px;
                top: var(--top1);

                transform:
                    scaleX(-1)
                    scale(var(--size));
            }
            45% {
                left: 100%;
                top: var(--top1);

                transform:
                    scaleX(-1)
                    scale(var(--size));
            }
            50% {
                left: 100%;
                top: var(--top2);

                transform:
                    scaleX(1)
                    scale(var(--size));
            }
            95% {
                left: -140px;
                top: var(--top2);

                transform:
                    scaleX(1)
                    scale(var(--size));
            }
            100% {
                left: -140px;
                top: var(--top1);

                transform:
                    scaleX(-1)
                    scale(var(--size));
            }
        }

        /* animate tail */
        @keyframes tail-wag {
            from {
                transform: rotate(12deg);
            }
            to {
                transform: rotate(-12deg);
            }
        }

        /* animate fin */
        @keyframes fin-flutter {
            from {
                transform: rotate(-10deg);
            }
            to {
                transform: rotate(15deg);
            }
        }
    """,
    js = """
        export default function(component) {
            const {
                data,
                parentElement
            } = component;

            /* find aquarium container */
            const container =
                parentElement.querySelector(
                    "#aquarium-container"
                );

            if (!container) {
                return;
            }

            /* insert html generated through python */
            container.innerHTML = data.html;
        }
    """
)