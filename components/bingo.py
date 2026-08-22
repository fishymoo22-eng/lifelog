import streamlit as st

bingo_component = st.components.v2.component(
    name = "bingo_board",
    html = """
        <div id="bingo-board-container"></div>
    """,
    css = """
        /* bingo board container */
        #bingo-board-container {
            width: 100%;
            max-width: 100%;

            box-sizing: border-box;

            margin: 0;
            padding: 0;

            border: 0.5px solid #aaa;

            overflow: hidden;
        }


        /* bingo grid */
        .bingo-grid {
            display: grid;

            grid-template-columns:
                repeat(5, minmax(0, 1fr));

            width: 100%;
            max-width: 100%;

            margin: 0;
            padding: 0;

            gap: 0;

            box-sizing: border-box;
        }


        /* individual bingo squares */
        .bingo-square {
            display: flex;

            flex-direction: column;

            align-items: center;
            justify-content: center;

            width: 100%;
            min-width: 0;

            aspect-ratio: 1 / 1;
            height: 75px;

            box-sizing: border-box;

            padding: 6px;
            margin: 0;

            /* thin interior lines */
            border: 0.25px solid #aaa;
            border-radius: 0;
            color: #222;

            text-align: center;
            overflow: hidden;
            overflow-wrap: anywhere;
            word-break: break-word;

            line-height: 1.2;

            cursor: pointer;

            appearance: none;
            -webkit-appearance: none;

            font-family: inherit;
        }

        /* dim hovered and clicked squares */
        .bingo-square:hover {
            filter: brightness(0.94);
        }
        .bingo-square:active {
            filter: brightness(0.88);
        }

        /* format completed squares */
        .bingo-square.completed {
            cursor: default;
        }
        .bingo-square.completed .bingo-title,
        .bingo-square.completed .bingo-progress {
            text-decoration: line-through;
        }
        .bingo-square.completed .bingo-progress s {
            text-decoration: none;
        }
        .bingo-square.completed:hover {
            filter: none;
        }

        /* bingo square text */
        .bingo-title {
            display: block;

            width: 100%;

            font-size: 0.9rem;
            font-weight: 400;

            overflow-wrap: anywhere;
            word-break: break-word;
        }

        /* bingo square progress text */
        .bingo-progress {
            display: block;

            margin-top: 5px;

            font-size: 0.9rem;
            font-weight: 400;

            flex-shrink: 0;
        }

        /* format mobile bingo correctly */
        @media (max-width: 640px) {

            .bingo-grid {
                width: 100%;

                grid-template-columns:
                    repeat(5, minmax(0, 1fr));
            }

            .bingo-square {
                padding: 3px;
            }

            .bingo-title {
                font-size: 0.75rem;

                line-height: 1.1;
            }

            .bingo-progress {
                margin-top: 3px;

                font-size: 0.75rem;
            }
        }
    """,
    js="""
        export default function(component) {

            const {
                data,
                parentElement,
                setTriggerValue
            } = component;

            /* find bingo board container */
            const container =
                parentElement.querySelector(
                    "#bingo-board-container"
                );

            if (!container) {
                return;
            }

            /* insert html generated through python */
            container.innerHTML = data.html;

            /* render click handler for incomplete squares only */
            const buttons =
                container.querySelectorAll(
                    ".bingo-square:not(.completed)"
                );

            buttons.forEach((button) => {
                button.onclick = (event) => {
                    event.preventDefault();

                    const bingoId =
                        button.getAttribute(
                            "data-bingo-id"
                        );

                    setTriggerValue(
                        "bingo_clicked",
                        bingoId
                    );
                };
            });
        }
    """
)