#pragma once

#ifndef __roofit_helper_hpp__
#define __roofit_helper_hpp__



// std
#include <string>
#include <iostream>

// extern
// NB: the external-constraint helpers need the fmt-style "format.hpp",
// which is not shipped with this repository.  Define
// ROOFIT_HELPER_WITH_FMT (and provide format.hpp) to enable them.
#ifdef ROOFIT_HELPER_WITH_FMT
#include "format.hpp"
#endif

// Root
#include "TROOT.h"
#include "TMatrixDSym.h"
#include "TLine.h"
#include "TPad.h"
#include "TAxis.h"
#include "TStyle.h"
#include "TPaveText.h"
#include "TLatex.h"

// RooFit basics
#include "RooWorkspace.h"
#include "RooRealVar.h"
#include "RooMultiVarGaussian.h"
#include "RooDataSet.h"
#include "RooPlot.h"
#include "RooHist.h"


namespace roofit_helper
{
  using namespace std;

#ifdef ROOFIT_HELPER_WITH_FMT
  using namespace fmt;

  auto add_external_variable(RooWorkspace *ws, string name, string varname, string value, string error, int std=2)
  {
    // Load
    const auto val = ws->var(value)->getValV();
    const auto err = ws->var(error)->getValV();
    
    // Add variable
    ws->factory(format(
        "{}[{},{},{}]",
        varname, val, val-std*err, val+std*err
    ).c_str());

    // Buld constraint
    ws->factory(format(
        "RooGaussian::{}({},{},{})",
        name, varname, val, err
    ).c_str());

    return ws->pdf(name);
  };

  auto add_external_variable(
    RooWorkspace *ws, string name, 
    string varname1, string value1, string error1,
    string varname2, string value2, string error2,
    string correlation, 
    int std=2
  )
  {
    auto v1  = ws->var(value1)->getValV();
    auto v2  = ws->var(value2)->getValV();
    auto e1  = ws->var(error1)->getValV();
    auto e2  = ws->var(error2)->getValV();
    auto cor = ws->var(correlation)->getValV();

    TMatrixDSym cov_matrix(2);
    {
      cov_matrix(0,0) =  1. * e1 * e1;
      cov_matrix(1,1) =  1. * e2 * e2;
      cov_matrix(1,0) = cor * e1 * e2;
      cov_matrix(0,1) = cov_matrix(1,0);
    };

    ws->factory(format("{0}[{1},{2},{3}]", varname1, v1, v1-std*e1, v1+std*e1));
    ws->factory(format("{0}[{1},{2},{3}]", varname2, v2, v2-std*e2, v2+std*e2));


    RooMultiVarGaussian constraint(
      name.c_str(), name.c_str(), 
      ws->argSet(format("{},{}", varname1, varname2)),
      ws->argSet(format("{},{}", value1  , value2  )),
      cov_matrix
    );

    ws->import(constraint);

    return ws->pdf(name);
  }
#endif  // ROOFIT_HELPER_WITH_FMT

  auto calculate_alpha_correction(const RooDataSet* dataset)
  {
    if (!dataset->isWeighted())
      return std::numeric_limits<double>::quiet_NaN();

    auto nEntries = dataset->numEntries();

    double sumw = 0, sumw2 = 0;
    for (auto i=0; i<nEntries; i++)
    {  
      auto event = dataset->get(i);
      auto weight = dataset->weight();
      sumw  += weight;
      sumw2 += weight*weight;
    };

    return sumw/sumw2;
  };

  auto calculate_alpha_correction(const RooDataSet* dataset, const string weight_name, const double scale)
  {
    auto nEntries = dataset->numEntries();

    double sumw = 0, sumw2 = 0;
    for (auto i=0; i<nEntries; i++)
    {  
      auto event = dataset->get(i);
      auto weight = event->getRealValue(weight_name.c_str()) * scale;
      sumw  += weight;
      sumw2 += weight*weight;
    };

    return sumw/sumw2;
  };

  // auto apply_alpha_correction(const RooDataSet* dataset)
  // {
    
  // };


  auto plot_with_pulls(RooPlot* rooplot, double r = 0.2) 
  {
    // Extract the range
    Double_t rangeMin = rooplot->GetXaxis()->GetXmin();
    Double_t rangeMax = rooplot->GetXaxis()->GetXmax();
    rooplot->SetTitle(" ");

    // Pulls creation
    RooHist* hpull = rooplot->pullHist();
    hpull->SetFillStyle(1001); //1001 (solid), 3013 (mesh)
    hpull->SetFillColor(kGray); //kGray, 39 (darker)
    
    RooPlot* pull = (RooPlot*)rooplot->emptyClone("pull");
    pull->SetTitle(" ");
    pull->SetMinimum(-5);
    pull->SetMaximum(5);
    pull->addPlotable(hpull,"E3");

    // Lines
    TLine* lineMiddle = new TLine(rangeMin, 0, rangeMax, 0);
    lineMiddle->SetLineWidth(1);
    lineMiddle->SetLineStyle(2);
    lineMiddle->SetLineColor(kBlack);
    pull->addObject(lineMiddle);
    TLine* lineUp = new TLine(rangeMin, 2, rangeMax, 2);
    lineUp->SetLineWidth(1);
    lineUp->SetLineStyle(2);
    lineUp->SetLineColor(kBlack);
    pull->addObject(lineUp);
    TLine* lineDown = new TLine(rangeMin, -2, rangeMax, -2);
    lineDown->SetLineWidth(1);
    lineDown->SetLineStyle(2);
    lineDown->SetLineColor(kBlack);
    pull->addObject(lineDown);

    // Canvas and Pad creation
    TPad *pad1 = new TPad("pad1", "Larger pad", 0.0, r , 1.0, 1.0);
    TPad *pad2 = new TPad("pad2", "Smaller pad", 0.0, 0.0, 1.0, r );

    // Margins
    pad1->SetLeftMargin(0.15);
    pad1->SetBottomMargin(0.14); //depends on the text size
    pad1->SetTopMargin(0.05);
    pad1->SetRightMargin(0.10);
    pad1->Draw();

    pad2->SetLeftMargin(0.15);
    pad2->SetBottomMargin(0.11);
    pad2->SetTopMargin(0.07);
    pad2->SetRightMargin(0.10);
    pad2->Draw();

    // Larger pad (distribution)
    pad1->cd();
    rooplot->GetYaxis()->SetTitleOffset(1.5);
    rooplot->GetXaxis()->SetTitleOffset(1.2);
    rooplot->GetYaxis()->SetLabelSize(0.05);
    rooplot->GetYaxis()->SetTitleSize(0.05);
    rooplot->GetXaxis()->SetLabelSize(0.05);
    rooplot->GetXaxis()->SetTitleSize(0.05);
    rooplot->Draw();

    // Smaller pad (pulls)
    pad2->cd();
    pull->GetYaxis()->SetTitleOffset(1.6);
    pull->GetYaxis()->SetTitle("");
    pull->GetYaxis()->SetLabelOffset(0.01);
    pull->GetYaxis()->SetNdivisions(504); //603, 504
    pull->GetYaxis()->SetLabelSize(0.04*1/r);// * (1-pad1->GetBottomMargin()) * (1-r) / r);
    pull->GetXaxis()->SetTitle("");
    pull->GetXaxis()->SetLabelSize(0);
    pull->Draw();

    pad1->cd();
  }

  auto set_variable_range(RooRealVar *var, string range_name)
  {
    auto [min,max] = var->getRange(range_name.c_str());
    var->setRange(min, max);
  };


  enum lhcbStyle_color
  {
    black  = 1,
    red    = 2,
    green  = 3,
    blue   = 4,
    yellow = 5,
    magenta= 6,
    cyan   = 7,
    purple = 9
  };

  void lhcbStyle()
  {
    ////////////////////////////////////////////////////////////////////
    // PURPOSE:
    //
    // This macro defines a standard style for (black-and-white) 
    // "publication quality" LHCb ROOT plots. 
    //
    // USAGE:
    //
    // Include the lines
    //   gROOT->ProcessLine(".L lhcbstyle.C");
    //   lhcbStyle();
    // at the beginning of your root macro.
    //
    // Example usage is given in myPlot.C
    //
    // COMMENTS:
    //
    // Font:
    // 
    // The font is chosen to be 132, this is Times New Roman (like the text of
    //  your document) with precision 2.
    //
    // "Landscape histograms":
    //
    // The style here is designed for more or less square plots.
    // For longer histograms, or canvas with many pads, adjustements are needed. 
    // For instance, for a canvas with 1x5 histograms:
    //  TCanvas* c1 = new TCanvas("c1", "L0 muons", 600, 800);
    //  c1->Divide(1,5);
    //  Adaptions like the following will be needed:
    //  gStyle->SetTickLength(0.05,"x");
    //  gStyle->SetTickLength(0.01,"y");
    //  gStyle->SetLabelSize(0.15,"x");
    //  gStyle->SetLabelSize(0.1,"y");
    //  gStyle->SetStatW(0.15);
    //  gStyle->SetStatH(0.5);
    //
    // Authors: Thomas Schietinger, Andrew Powell, Chris Parkes, Niels Tuning
    // Maintained by Editorial board member (currently Niels)
    ///////////////////////////////////////////////////////////////////

    // Use times new roman, precision 2 
    Int_t lhcbFont        = 132;  // Old LHCb style: 62;
    // Line thickness
    Double_t lhcbWidth    = 2.00; // Old LHCb style: 3.00;
    // Text size
    Double_t lhcbTSize    = 0.06;
    
    // use plain black on white colors
    gROOT->SetStyle("Plain"); 
    TStyle *lhcbStyle= new TStyle("lhcbStyle","LHCb plots style");
    
    //lhcbStyle->SetErrorX(0); //  don't suppress the error bar along X

    lhcbStyle->SetFillColor(1);
    lhcbStyle->SetFillStyle(1001);   // solid
    lhcbStyle->SetFrameFillColor(0);
    lhcbStyle->SetFrameBorderMode(0);
    lhcbStyle->SetPadBorderMode(0);
    lhcbStyle->SetPadColor(0);
    lhcbStyle->SetCanvasBorderMode(0);
    lhcbStyle->SetCanvasColor(0);
    lhcbStyle->SetStatColor(0);
    lhcbStyle->SetLegendBorderSize(0);
    lhcbStyle->SetLegendFont(132);

    // If you want the usual gradient palette (blue -> red)
    lhcbStyle->SetPalette(1);
    // If you want colors that correspond to gray scale in black and white:
    int colors[8] = {0,5,7,3,6,2,4,1};
    lhcbStyle->SetPalette(8,colors);

    // set the paper & margin sizes
    lhcbStyle->SetPaperSize(20,26);
    lhcbStyle->SetPadTopMargin(0.05);
    lhcbStyle->SetPadRightMargin(0.05); // increase for colz plots
    lhcbStyle->SetPadBottomMargin(0.16);
    lhcbStyle->SetPadLeftMargin(0.14);
    
    // use large fonts
    lhcbStyle->SetTextFont(lhcbFont);
    lhcbStyle->SetTextSize(lhcbTSize);
    lhcbStyle->SetLabelFont(lhcbFont,"x");
    lhcbStyle->SetLabelFont(lhcbFont,"y");
    lhcbStyle->SetLabelFont(lhcbFont,"z");
    lhcbStyle->SetLabelSize(lhcbTSize,"x");
    lhcbStyle->SetLabelSize(lhcbTSize,"y");
    lhcbStyle->SetLabelSize(lhcbTSize,"z");
    lhcbStyle->SetTitleFont(lhcbFont);
    lhcbStyle->SetTitleFont(lhcbFont,"x");
    lhcbStyle->SetTitleFont(lhcbFont,"y");
    lhcbStyle->SetTitleFont(lhcbFont,"z");
    lhcbStyle->SetTitleSize(1.2*lhcbTSize,"x");
    lhcbStyle->SetTitleSize(1.2*lhcbTSize,"y");
    lhcbStyle->SetTitleSize(1.2*lhcbTSize,"z");

    // use medium bold lines and thick markers
    lhcbStyle->SetLineWidth(lhcbWidth);
    lhcbStyle->SetFrameLineWidth(lhcbWidth);
    lhcbStyle->SetHistLineWidth(lhcbWidth);
    lhcbStyle->SetFuncWidth(lhcbWidth);
    lhcbStyle->SetGridWidth(lhcbWidth);
    lhcbStyle->SetLineStyleString(2,"[12 12]"); // postscript dashes
    lhcbStyle->SetMarkerStyle(20);
    lhcbStyle->SetMarkerSize(1.0);

    // label offsets
    lhcbStyle->SetLabelOffset(0.010,"X");
    lhcbStyle->SetLabelOffset(0.010,"Y");

    // by default, do not display histogram decorations:
    lhcbStyle->SetOptStat(0);  
    //lhcbStyle->SetOptStat("emr");  // show only nent -e , mean - m , rms -r
    // full opts at http://root.cern.ch/root/html/TStyle.html#TStyle:SetOptStat
    lhcbStyle->SetStatFormat("6.3g"); // specified as c printf options
    lhcbStyle->SetOptTitle(0);
    lhcbStyle->SetOptFit(0);
    //lhcbStyle->SetOptFit(1011); // order is probability, Chi2, errors, parameters
    //titles
    lhcbStyle->SetTitleOffset(0.95,"X");
    lhcbStyle->SetTitleOffset(0.95,"Y");
    lhcbStyle->SetTitleOffset(1.2,"Z");
    lhcbStyle->SetTitleFillColor(0);
    lhcbStyle->SetTitleStyle(0);
    lhcbStyle->SetTitleBorderSize(0);
    lhcbStyle->SetTitleFont(lhcbFont,"title");
    lhcbStyle->SetTitleX(0.0);
    lhcbStyle->SetTitleY(1.0); 
    lhcbStyle->SetTitleW(1.0);
    lhcbStyle->SetTitleH(0.05);
    
    // look of the statistics box:
    lhcbStyle->SetStatBorderSize(0);
    lhcbStyle->SetStatFont(lhcbFont);
    lhcbStyle->SetStatFontSize(0.05);
    lhcbStyle->SetStatX(0.9);
    lhcbStyle->SetStatY(0.9);
    lhcbStyle->SetStatW(0.25);
    lhcbStyle->SetStatH(0.15);

    // put tick marks on top and RHS of plots
    lhcbStyle->SetPadTickX(1);
    lhcbStyle->SetPadTickY(1);

    // histogram divisions: only 5 in x to avoid label overlaps
    lhcbStyle->SetNdivisions(505,"x");
    lhcbStyle->SetNdivisions(510,"y");
    
    gROOT->SetStyle("lhcbStyle");
    gROOT->ForceStyle();

    // add LHCb label
    TPaveText* lhcbName = new TPaveText(gStyle->GetPadLeftMargin() + 0.05,
                                        0.87 - gStyle->GetPadTopMargin(),
                                        gStyle->GetPadLeftMargin() + 0.20,
                                        0.95 - gStyle->GetPadTopMargin(),
                                        "BRNDC"); //left
    lhcbName = new TPaveText(0.89 - gStyle->GetPadLeftMargin(),
                                        0.87 - gStyle->GetPadTopMargin(),
                                        1.05 - gStyle->GetPadLeftMargin(),
                                        0.95 - gStyle->GetPadTopMargin(),
                                        "BRNDC"); //right                                 
    lhcbName->AddText("LHCb");
    lhcbName->SetFillColor(0);
    lhcbName->SetTextAlign(12);
    lhcbName->SetBorderSize(0);

    TText *lhcbLabel = new TText();
    lhcbLabel->SetTextFont(lhcbFont);
    lhcbLabel->SetTextColor(1);
    lhcbLabel->SetTextSize(lhcbTSize);
    lhcbLabel->SetTextAlign(12);

    TLatex *lhcbLatex = new TLatex();
    lhcbLatex->SetTextFont(lhcbFont);
    lhcbLatex->SetTextColor(1);
    lhcbLatex->SetTextSize(lhcbTSize);
    lhcbLatex->SetTextAlign(12);

  }


}




#endif