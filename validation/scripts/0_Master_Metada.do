*** MASTER DO FILE
*** Run this file to replicate the figures and estimates in Albers and Kappner (2021)

clear all
set more off

*** Set user
global user "USER"

*** Define paths to data and scripts for specified user

if "${user}"=="USER" {
	global rootfolder 			"/berlin-city-directory/validation/"
	global githubfolder			"/Users/thiloalbers/GitHub/"
	global rsuitefolder			"/usr/local/bin/r" 
	}
		
global temp 		"$rootfolder/temp"
global scripts 		"$rootfolder/scripts"
global rawdata 		"$rootfolder/data"
global output		"$rootfolder/final output"
	 	
*** Store figures in final output directory
cd "$rootfolder/Work/Final Output"


* Necessary packages 

	* install colour scheme for graphs 
		*net install scheme-modern, from("https://raw.githubusercontent.com/mdroste/stata-scheme-modern/master/")

	* install gpinter 
		* install rsource - you can run r in stata with this.  
		* install gpinter - an exact description how to implement this in stata can be found on Thomas Blanchet's github: https://github.com/thomasblanchet/gpinter

*** Graph settings
	set graphics         on
	set autotabgraphs    on
	set scheme           modern
	set printcolor	   	 automatic
	set copycolor        automatic



*** Do files

	* data preperation
		do	"$scripts/1_DataPrep_DirectorySpread.do"
		do	"$scripts/2_DataPrep_ValidationTopIncomes.do"
		
	* tables and figures
		do	"$scripts/3_DirectorySpread.do"
		do	"$scripts/4_Validation.do"
