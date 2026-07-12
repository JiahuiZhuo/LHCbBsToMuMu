rule all:
    input:
        "figures/mass_fit.png",


# The inputs are marked ancient() so that file timestamps never trigger a
# re-selection: results/selected_data.root is committed to git, and a fresh
# clone has scrambled timestamps (running the selection there would fail --
# the raw data is not in the repository).  After changing config.yaml or the
# script, re-run explicitly with:  snakemake -R selection --cores 16
rule selection:
    input:
        script=ancient("src/selection.py"),
        config=ancient("config.yaml"),
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
