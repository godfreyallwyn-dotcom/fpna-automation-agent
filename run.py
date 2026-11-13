#!/usr/bin/env python3
"""One command: python run.py  ->  Excel pack + Power BI dataset + PowerPoint MIS deck."""
from __future__ import annotations

import argparse
from pathlib import Path

from fpna_agent.agent import Agent
from fpna_agent.config import Config
from fpna_agent.sample_data import generate


def main() -> int:
    ap = argparse.ArgumentParser(description="Agentic FP&A workflow")
    ap.add_argument("--input", default="data/input", help="folder with the input files")
    ap.add_argument("--output", default="output", help="folder for deliverables")
    ap.add_argument("--no-llm", action="store_true", help="force the offline rule-based planner and template commentary")
    ap.add_argument("--generate-sample", action="store_true", help="(re)create the synthetic sample input pack first")
    a = ap.parse_args()
    inp = Path(a.input)
    if a.generate_sample or not (inp / "gl_actuals.csv").exists():
        print(f"Generating sample input pack in {inp} ...")
        generate(inp)
    cfg = Config(input_dir=inp, output_dir=Path(a.output), use_llm=not a.no_llm)
    st = Agent(cfg).run()
    print("\nDone." if st.outputs else "\nRun did not produce deliverables - see output/agent_trace.md")
    for k, v in st.outputs.items(): print(f"  {k:8s} {v}")
    for w in st.warnings: print("  warning:", w)
    return 0 if st.outputs else 1


if __name__ == "__main__":
    raise SystemExit(main())
