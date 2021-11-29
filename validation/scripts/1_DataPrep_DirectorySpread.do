*** PREPARE DATA FOR FIGURE 1
*** Run this file to prepare the data for Figure 1

clear

*** Load metadata
import excel "$rawdata/Directories of directories/Directories_Meta_Data.xlsx", sheet("Sheet1") firstrow
drop if City==""

*** Assume latest is in 1910 if not explicitly stated
replace Dateoflatestadressbook=1910 if Dateoflatestadressbook==. 
save  "$temp/directories", replace

*** Create time vector
import excel "$rawdata/YEAR_TEMP/Yeartemplate.xlsx", sheet("Sheet1") firstrow clear
save  "$temp/timevector", replace

*** Generate world cities dataset from Clio data
foreach x in "europe" "africa" "america"  "asia-australia"   {
	import excel "$rawdata/Population (Clio Infra)/CLIO-INFRA EDITED/def_`x'", clear firstrow		  
	save "$temp/pop_`x'", replace	
}

*** Append and clean 
clear
foreach x in "europe" "africa" "america"  "asia-australia"   {
	append using "$temp/pop_`x'.dta", force
	}

drop y1950 y2000
drop if City==""
save "$temp/world_bairoch", replace
		 
*** Merge 
merge 1:1 City using "$temp/directories"
drop _merge
save "$temp/directories_Bairoch", replace