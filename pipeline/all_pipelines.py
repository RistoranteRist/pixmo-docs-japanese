import os
import pickle

from datadreamer import DataDreamer
from datadreamer.llms import OpenAI
from datadreamer.steps import concat

from pipeline.utils.anthropic_support import CustomAnthropic

from .graphviz_diagram_pipeline import GraphvizDiagramPipeline
from .html_chart_pipeline import HTMLChartPipeline
from .html_document_pipeline import HTMLDocumentPipeline
from .html_table_pipeline import HTMLTablePipeline
from .latex_chart_pipeline import LaTeXChartPipeline
from .latex_diagram_pipeline import LaTeXDiagramPipeline
from .latex_document_pipeline import LaTeXDocumentPipeline
from .latex_table_pipeline import LaTeXTablePipeline
from .matplotlib_chart_pipeline import MatplotlibChartPipeline
from .mermaid_diagram_pipeline import MermaidDiagramPipeline
from .plotly_chart_pipeline import PlotlyChartPipeline
from .plotly_table_pipeline import PlotlyTablePipeline
from .vegalite_chart_pipeline import VegaLiteChartPipeline


def run_datadreamer_session(args):
    if args.qa:
        os.environ["GENERATE_QA"] = "true"
    else:
        os.environ["GENERATE_QA"] = "false"
 
    with DataDreamer("./session_output"):
        # Load GPT-4
        gpt_4o = OpenAI(
            model_name="gpt-4o",
            api_key=args.openai_api_key,
            system_prompt="You are a helpful data scientist.",
        )

        gpt_4o_mini = OpenAI(
            model_name="gpt-4o-mini",
            api_key=args.openai_api_key,
            system_prompt="You are a helpful data scientist.",
        )

        claude_sonnet = CustomAnthropic(
            model_name="claude-3-5-sonnet-20240620",
            api_key=args.anthropic_api_key,
        )

        if args.llm == "gpt-4o": llm = gpt_4o
        elif args.llm == "claude-sonnet": llm = claude_sonnet
        elif args.llm == "gpt-4o-mini": llm = gpt_4o_mini

        if args.code_llm == "gpt-4o": code_llm = gpt_4o
        elif args.code_llm == "claude-sonnet": code_llm = claude_sonnet
        elif args.code_llm == "gpt-4o-mini": code_llm = gpt_4o_mini

        # Choose which pipelines to run
        pipelines = {
            "Generate Matplotlib Charts": MatplotlibChartPipeline,
            "Generate Vega-Lite Charts": VegaLiteChartPipeline,
            "Generate Plotly Charts": PlotlyChartPipeline,
            "Generate LaTeX Charts": LaTeXChartPipeline,
            "Generate HTML Charts": HTMLChartPipeline,
            "Generate LaTeX Tables": LaTeXTablePipeline,
            "Generate Plotly Tables": PlotlyTablePipeline,
            "Generate HTML Tables": HTMLTablePipeline,
            "Generate LaTeX Documents": LaTeXDocumentPipeline,
            "Generate HTML Documents": HTMLDocumentPipeline,
            "Generate Graphviz Diagrams": GraphvizDiagramPipeline,
            "Generate LaTeX Diagrams": LaTeXDiagramPipeline,
            "Generate Mermaid Diagrams": MermaidDiagramPipeline,
        }
        pipelines = {
            k: v
            for k, v in pipelines.items()
            if v.__name__ in [p.strip() for p in args.pipelines.split(",")]
        }

        # Choose how many visualizes per pipeline
        if "," in args.num:
            nums = [int(n.strip()) for n in args.num.strip(",")]
            assert len(nums) == len(pipelines)
        else:
            nums = [int(args.num)] * len(pipelines)
        
        # Get figure types
        figure_types = [figure_type.strip() for figure_type in args.types.split(",")]

        # Run each selected pipeline
        synthetic_visuals = [
            pipeline(
                pipeline_name,
                args={
                    "llm": llm,
                    "code_llm": code_llm,
                    "batch_size": args.batch_size,
                    "code_batch_size": args.code_batch_size,
                    "n": num,
                    "seed": args.seed,
                    "figure_types": figure_types,
                    "qa": args.qa,
                },
                force=args.force,
            )
            for num, (pipeline_name, pipeline) in zip(nums, pipelines.items())
        ]

        # Combine results from each pipeline
        scifi_dataset = concat(
            *synthetic_visuals, name="Combine results from all pipelines"
        )

        # Preview n rows of the dataset
        print(scifi_dataset.head(n=5))

        output_dict = scifi_dataset.export_to_dict()
        # 保存
        with open(f'{args.name}.pkl', "wb") as f:
            pickle.dump(output_dict, f)

        # scifi_dataset.export_to_json(f'{args.name}.json')
        # Push to HuggingFace Hub
        # scifi_dataset.publish_to_hf_hub(args.name, private=True)
