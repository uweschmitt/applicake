#! /usr/bin/env Rscript

#setwd("/cluster/apps/imsbtools/20120119/bin/")

args <- commandArgs(TRUE)
print(args)
if (length(args)>=4){
  lfq.generator.properties <- args[1]
  peptides.csv <- args[2]
  proteins.csv <- args[3]
  username <- args[4]
print(username)
}else{
  print("setting defaults")
  lfq.generator.properties <- "lfq_generator.properties"
  peptides.csv <- "peptides.csv"
  proteins.csv <- "proteins.csv"
  username <- "dummy blummy"
}

print("START")
print(lfq.generator.properties)
print(peptides.csv)
print(proteins.csv)

initial.options <- commandArgs(trailingOnly = FALSE)
file.arg.name <- "--file="
script.name <- sub(file.arg.name, "", initial.options[grep(file.arg.name, initial.options)])
script.basename <- dirname(script.name)
other.name <- paste(sep="/", script.basename, "analyseLFQ.Snw")
print(other.name)
Sweave(other.name)
tools::texi2dvi("analyseLFQ.tex",pdf=TRUE)
