rule all:
    input:
        "figures/mass_fit.png",


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
