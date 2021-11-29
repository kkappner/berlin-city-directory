*** PRODUCE FIGURE 1
*** Run this file to produce Figure 1

clear  
use "$temp/directories_Bairoch"

*** top 50 US cities in 1900

preserve 
	
	keep if ContinentRegionCountry=="United States"
	gen inbook=1 if In_clio=="yes" 
	replace inbook=1 if   Publishes_in_1913==1
	replace  inbook=0 if  inbook==.
	drop if y1900==.

	gsort -y1900

	drop if _n>50

	keep Dateoff
	 
	sort Dateoff

	gen sum_active=_n

	rename Dateoff year

	collapse (last) sum_active , by(year)

	*** Add time vector
	
	merge 1:1 year using "$temp/timevector"
	
	drop _merge
	 
	sort year
	
	replace sum_active=sum_active[_n-1] if sum_active==.
	 
	gen share_top50US=100*sum_active/50
	 
	drop sum_active
	tsset year
	 
	save "$temp/top50_US", replace	 
		 
restore
				

* top 20 world cities 

preserve

	gen inbook=1 if In_clio=="yes" 
	replace inbook=1 if   Publishes_in_1913==1
	replace  inbook=0 if  inbook==.
	drop if y1900==.

	gsort -y1900

	drop if _n>20
	
	keep Dateoff
	
	sort Dateoff

	gen sum_active=_n

	rename Dateoff year

	collapse (last) sum_active , by(year)

	*** Add time vector
	
	merge 1:1 year using "$temp/timevector"
	
	drop _merge
	 
	sort year
	
	replace sum_active=sum_active[_n-1] if sum_active==.
	 
	gen share_top20world=100*(sum_active/20)
	 
	drop sum_active
	tsset year
	 
	save "$temp/top20_WORLD", replace
				 
restore 			 		

clear 

set scheme sj
use "$temp/top20_WORLD"

merge 1:1 year using "$temp/top50_US"
drop _merge
		

foreach x in share_top20world share_top50US {
	replace `x'=0 if `x'==.
}
	
gen housenumbering =100 if tin(1733,1800)
gen printingpress =100  if tin(1454,1500)

foreach x in printingpress housenumbering {
	replace `x'=0 if `x'==.
}

label var  share_top20world "20 largest world cities" 
label var  share_top50US 	"50 largest US cities" 
label var  housenumbering   "Initial spread of house numbering" 
label var  printingpress   	"Initial spread of printing press" 

twoway	( area printingpress year if printingpress == 100,  xsize(8) color(gs6))   ( area housenumbering year if housenumbering == 100,  color(gs6))  (line share_top20world year)   (line share_top50US year) ///
, legend(  order(3 "20 largest world cities" 4 "50 largest US cities")  size(mediumsmall) ring(0) position(2) bmargin(large) col(2)) ytitle("Proportion of cities with directories in %", size(medsmall)) ///
bgcolor(white)  graphregion(color(white))   xtitle("Year") xlabel(1450(50)1900) text( 103 1500 "Spread of printing press", size(small)) text( 103 1770 "Spread of house numbering", size(small))  ylab(0(10)100, nogrid)

graph export "$output/Figures/directory_spread.pdf", replace