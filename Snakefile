rule all:
    input:
        "figures/mass_fit.png",
        "figures/mass_plot.png",


rule selection:
    input:
        script="src/selection.py",
        config="config.yaml",
    output:
        "results/selected_data.root",
    threads: 16
    shell:
        "python {input.script} --config {input.config} --output {output} --threads {threads}"


rule mass_fit:
    input:
        script="src/mass_fit.py",
        helper="src/roofit_helper.hpp",
        data="results/selected_data.root",
    output:
        "figures/mass_fit.png",
    shell:
        "python {input.script} --input {input.data} --output {output}"


rule mass_plot:
    input:
        data="results/selected_data.root",
        helper="src/roofit_helper.hpp",
    output:
        "figures/mass_plot.png",
    log:
        notebook="logs/mass_plot.ipynb",
    notebook:
        "notebooks/mass_plot.ipynb"
