*** MASTER DO FILE
*** Run this file to replicate the figures and estimates in Albers and Kappner (2021)

clear all
set more off

*** Set user
global user "Thilo"
*global user "Thilo_HOME"
*global user "Thilo"

*** Define paths to data and scripts
if "${user}"=="Thilo_HOME" {
	global rootfolder 			"/Users/thiloalbers/Dropbox/!Adress books and Census data"
	global githubfolder			"/Users/thiloalbers/GitHub/"
	global rsuitefolder			 "/Library/Frameworks/R.framework/Versions/3.6/Resources/bin/R" 
	}
	
if "${user}"=="Thilo" {
	global rootfolder 			"/Users/thiloalbers/Dropbox/!Adress books and Census data"
	global githubfolder			"/Users/thiloalbers/GitHub/"
	global rsuitefolder			 "/usr/local/bin/r" 
	}
	
if "${user}"=="Kalle" {
	global rootfolder 			"/Users/kalle/Dropbox/!Adress books and Census data"
}
		
global temp 		"$rootfolder/Work/Temp"
global scripts 		"$rootfolder/Work/Scripts"
global rawdata 		"$rootfolder/Data"
global output		"$rootfolder/Work/Final Output"
	 	
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
	
	
	
	
	
