*** VALIDATION FIGURES AND ESTIMATES
*** Run this file to produce Figures 5 to 8.

* Prepare matching census-level dataset
import delimited "$rawdata/validation_berlin_ab1880/pop_1880.csv", clear
replace id=116 if id==1161
replace id=162 if id==1621
replace id=162 if id==1622
replace id=184 if id==1841
replace id=184 if id==1842
replace id=111 if id==1111
replace id=111 if id==1112
collapse (sum) pop_t hh_t, by(id)
save "$temp/pop_1880.dta", replace

*** sb_1: ArcGIS-based geocoding
*** sb_2: Street-interpolation-based geocoding
*** sb_3: Exact/manual geocoding
*** hiscam_1: Fuzzy match from HISCO website
*** hiscam_2: Prussian census coding
*** hiscam_3: Comprehensive list-based occupation matching

*** Compute HISCAM counts and means
forval hiscam_i = 1/3 {
	forval sb_i = 1/3 	{
		foreach stat in "count" "mean" {

			use "$rawdata/validation_berlin_ab1880/validation_ab.dta", clear
			destring sb_`sb_i', replace
			replace sb_`sb_i'=116 if sb_`sb_i'==1161
			replace sb_`sb_i'=162 if sb_`sb_i'==1621
			replace sb_`sb_i'=162 if sb_`sb_i'==1622
			replace sb_`sb_i'=184 if sb_`sb_i'==1841
			replace sb_`sb_i'=184 if sb_`sb_i'==1842
			replace sb_`sb_i'=111 if sb_`sb_i'==1111
			replace sb_`sb_i'=111 if sb_`sb_i'==1112
			collapse (`stat') hiscam_`hiscam_i', by(sb_`sb_i')
			
			rename sb_`sb_i' id
			rename hiscam_`hiscam_i' hiscam_`stat'_`hiscam_i'_`sb_i'
			label variable hiscam_`stat'_`hiscam_i'_`sb_i' "HISCAM (`stat') for tract definition `sb_i' and hiscam definition `hiscam_i'"
			keep id hiscam_`stat'_`hiscam_i'_`sb_i'
			destring id, replace
			save "$temp/ab_1880_collapsed_`stat'_`hiscam_i'_`sb_i'.dta", replace
		
		}
	}		
}

*** Compute HISCAM mass top shares by Stadtbezirk
forval hiscam_i = 1/3 {
	forval sb_i = 1/3 	{

			use "$rawdata/validation_berlin_ab1880/validation_ab.dta", clear
			destring sb_`sb_i', replace
			replace sb_`sb_i'=116 if sb_`sb_i'==1161
			replace sb_`sb_i'=162 if sb_`sb_i'==1621
			replace sb_`sb_i'=162 if sb_`sb_i'==1622
			replace sb_`sb_i'=184 if sb_`sb_i'==1841
			replace sb_`sb_i'=184 if sb_`sb_i'==1842
			replace sb_`sb_i'=111 if sb_`sb_i'==1111
			replace sb_`sb_i'=111 if sb_`sb_i'==1112
			rename sb_`sb_i' id
			
			levelsof id, local(STADTBEZIRKE)
			foreach BEZIRK of local STADTBEZIRKE{
				
				preserve
				keep if id == `BEZIRK'
				sort hiscam_`hiscam_i'
				drop if hiscam_`hiscam_i' == .
				gen n = _n
				
				qui count
				if `r(N)' > 100 {
					forval share_i = 30/99 {
						qui count
						gen pct_`share_i' = _n / `r(N)'
						qui  total hiscam_`hiscam_i' if pct_`share_i' >= (`share_i'/100)
						local mass1 = _b[hiscam_`hiscam_i']
						qui total hiscam_`hiscam_i'
						local mass2 = _b[hiscam_`hiscam_i']
						gen hiscam_share_`hiscam_i'_`sb_i'_`share_i' = `mass1'/`mass2'		
						}

					}
				else {
					forval share_i = 30/99 {
						gen hiscam_share_`hiscam_i'_`sb_i'_`share_i' = .
						}
					}
				
					keep if _n==1
					keep id hiscam_share_*_*_*
					save "$temp/hiscam_topshare_`hiscam_i'_`sb_i'_b`BEZIRK'" , replace
					restore				
			}
	}
}

*** Sort estimates by top share
forval hiscam_i = 1/3 {
	forval sb_i = 1/3 {
		forval share_i = 30/99 {
			clear
			set obs 1
			generate id = .
			generate hiscam_share_`hiscam_i'_`sb_i'_`share_i' = .
			save "$temp/hiscam_topshare_`hiscam_i'_`sb_i'_s`share_i'" , replace
			
			use "$rawdata/validation_berlin_ab1880/validation_ab.dta", clear
			destring sb_`sb_i', replace
			replace sb_`sb_i'=116 if sb_`sb_i'==1161
			replace sb_`sb_i'=162 if sb_`sb_i'==1621
			replace sb_`sb_i'=162 if sb_`sb_i'==1622
			replace sb_`sb_i'=184 if sb_`sb_i'==1841
			replace sb_`sb_i'=184 if sb_`sb_i'==1842
			replace sb_`sb_i'=111 if sb_`sb_i'==1111
			replace sb_`sb_i'=111 if sb_`sb_i'==1112
			
			levelsof sb_`sb_i', local(STADTBEZIRKE)
			foreach BEZIRK of local STADTBEZIRKE{
				use "$temp/hiscam_topshare_`hiscam_i'_`sb_i'_b`BEZIRK'", clear
				keep hiscam_share_`hiscam_i'_`sb_i'_`share_i'
				gen id = `BEZIRK'
				save "$temp/TEMP_TOPSHARE$", replace
				use "$temp/hiscam_topshare_`hiscam_i'_`sb_i'_s`share_i'", clear
				append using "$temp/TEMP_TOPSHARE$"
				save "$temp/hiscam_topshare_`hiscam_i'_`sb_i'_s`share_i'", replace
			}
		}
	}
}
 
*** Merge all data
use "$temp/income_1880.dta", clear
merge 1:1 id using "$temp/pop_1880.dta", nogenerate 
merge 1:1 id using "$temp/top_shares_BERLIN.dta", nogenerate 
forval hiscam_i = 1/3 {
	forval sb_i = 1/3 	{
		foreach stat in "count" "mean" {
			merge 1:1 id using "$temp/ab_1880_collapsed_`stat'_`hiscam_i'_`sb_i'.dta", nogenerate
		}
		
		forval share_i = 30/99  {
			merge 1:1 id using "$temp/hiscam_topshare_`hiscam_i'_`sb_i'_s`share_i'", nogenerate
			
		}
 		
	}
}

drop if id == .

*** Plot tract-level count correlations (Figure 5)
*** Get logs
foreach var in "hiscam_count_1_1" "hiscam_count_2_1" "hiscam_count_3_1" "hiscam_count_1_2" "hiscam_count_2_2" "hiscam_count_3_2" "hiscam_count_1_3" "hiscam_count_2_3" "hiscam_count_3_3" "hh_t" {
	gen ln_`var' = ln(`var')
}

*** number of obs
*** spearman hiscam_count_1_1 hh_t (for auto- auto)
*** spearman hiscam_count_2_1 hh_t (all others)
forval sb_i = 1/3 {

*** Graph titles
		 
	if "`sb_i'"=="1" {
		local name_graph  "Automatic GR and..."
		}		
	if "`sb_i'"=="2" {
		local name_graph  "Semi-automatic GR and..."
		}
	if "`sb_i'"=="3" {
		local name_graph  "Manual GR and..."
		}
		 
	forvalues hiscam_i = 1/3 {
		qui spearman hiscam_count_`hiscam_i'_`sb_i' hh_t
		scalar s`hiscam_i'_`sb_i' = r(rho)
		local S`hiscam_i'_`sb_i' : di %6.2f scalar(s`hiscam_i'_`sb_i')
		}
		
	twoway  (function y=x, range(0 8.5) lpattern(dot) lcolor(black%50)) ///
			(scatter ln_hh_t ln_hiscam_count_1_`sb_i', color(gray) msymbol(X)) (scatter ln_hh_t ln_hiscam_count_2_`sb_i', color(gray) msymbol(Oh)) (scatter ln_hh_t ln_hiscam_count_3_`sb_i', msymbol(Oh) color(black)) ///
			(lfit ln_hh_t ln_hiscam_count_1_`sb_i', lpattern(dash) lcolor(gray)) (lfit ln_hh_t ln_hiscam_count_2_`sb_i', lcolor(gray)) (lfit ln_hh_t ln_hiscam_count_3_`sb_i', lcolor(black)), ///
			legend(order(2 "automatic SR (rho =`S1_`sb_i'')" 3 "semi-automatic SR (rho =`S2_`sb_i'')" 4 "manual SR (rho =`S3_`sb_i'')") size(small) col(1) ring(100) position(12)  region(fcolor(white))   subtitle("`name_graph'")) ///
			xscale(r(0 8.5)) xlabel(0(2)8.5) ///
			yscale(r(0 8.5)) ylabel(0(2)8.5) ///
			bgcolor(white) graphregion(color(white))
			graph save "$output/Figures/validation_count_`sb_i'", replace
}
graph combine "$output/Figures/validation_count_1" "$output/Figures/validation_count_2" "$output/Figures/validation_count_3", r(1) graphregion(color(white))   l1("Ln of households counted in census", size(small)) b1("Ln of referenced directory entries", size(small)) imargin(zero)  
graph export "$output/Figures/validation_count_combined.pdf" , replace 

*** Plot tract-level means correlations (Figure 6)
*** Get logs
foreach var in "hiscam_mean_1_1" "hiscam_mean_2_1" "hiscam_mean_3_1" "hiscam_mean_1_2" "hiscam_mean_2_2" "hiscam_mean_3_2" "hiscam_mean_1_3" "hiscam_mean_2_3" "hiscam_mean_3_3" "income" {
	gen ln_`var' = ln(`var')
}

forval sb_i = 1/3 {

*** Graph titles
		 
	if "`sb_i'"=="1" {
		local name_graph  "Automatic GR and..."
		}		
	if "`sb_i'"=="2" {
		local name_graph  "Semi-automatic GR and..."
		}
	if "`sb_i'"=="3" {
		local name_graph  "Manual GR and..."
		}
		 
	forvalues hiscam_i = 1/3 {
		qui spearman hiscam_mean_`hiscam_i'_`sb_i' income
		scalar s`hiscam_i'_`sb_i' = r(rho)
		local S`hiscam_i'_`sb_i' : di %6.2f scalar(s`hiscam_i'_`sb_i')
		}
		
	twoway  (scatter ln_income ln_hiscam_mean_1_`sb_i', color(gray) msymbol(X)) (scatter ln_income ln_hiscam_mean_2_`sb_i', color(gray) msymbol(Oh)) (scatter ln_income ln_hiscam_mean_3_`sb_i', msymbol(Oh) color(black)) ///
			(lfit ln_income ln_hiscam_mean_1_`sb_i', lpattern(dash) lcolor(gray)) (lfit ln_income ln_hiscam_mean_2_`sb_i', lcolor(gray)) (lfit ln_income ln_hiscam_mean_3_`sb_i', lcolor(black)), ///
			legend(order(1 "automatic SR (rho =`S1_`sb_i'')" 2 "semi-automatic SR (rho =`S2_`sb_i'')" 3 "manual SR (rho =`S3_`sb_i'')") size(small) col(1) ring(100) position(12)  region(fcolor(white))   subtitle("`name_graph'")) ///
			xscale(r(3.9 4.4)) xlabel(3.9(0.1)4.4) ///
			yscale(r(4.5 8.1)) ylabel(4.5(.5)8.1) ///
			bgcolor(white) graphregion(color(white))
			graph save "$output/Figures/validation_mean_`sb_i'", replace
}
graph combine "$output/Figures/validation_mean_1" "$output/Figures/validation_mean_2" "$output/Figures/validation_mean_3", r(1) graphregion(color(white))   l1("Ln of average income (Reichsmark per year)", size(small)) b1("Ln of average HISCAM value", size(small)) imargin(zero)  
graph export "$output/Figures/validation_mean_combined.pdf" , replace 

*** Plot tract-level top50 share correlations (Figure 7)
forval sb_i = 1/3 {

*** Graph titles
		 
	if "`sb_i'"=="1" {
		local name_graph  "Automatic GR and..."
		}		
	if "`sb_i'"=="2" {
		local name_graph  "Semi-automatic GR and..."
		}
	if "`sb_i'"=="3" {
		local name_graph  "Manual GR and..."
		}
		 
	forvalues hiscam_i = 1/3 {
		qui spearman hiscam_share_`hiscam_i'_`sb_i'_50 top_share50
		scalar s`hiscam_i'_`sb_i' = r(rho)
		local S`hiscam_i'_`sb_i' : di %6.2f scalar(s`hiscam_i'_`sb_i')
		}
		
	twoway  (scatter top_share50 hiscam_share_1_`sb_i'_50, color(gray) msymbol(X)) (scatter top_share50 hiscam_share_2_`sb_i'_50, color(gray) msymbol(Oh)) (scatter top_share50 hiscam_share_3_`sb_i'_50, msymbol(Oh) color(black)) ///
			(lfit top_share50 hiscam_share_1_`sb_i'_50, lpattern(dash) lcolor(gray)) (lfit top_share50 hiscam_share_2_`sb_i'_50, lcolor(gray)) (lfit top_share50 hiscam_share_3_`sb_i'_50, lcolor(black)), ///
			legend(order(1 "automatic SR (rho =`S1_`sb_i'')" 2 "semi-automatic SR (rho =`S2_`sb_i'')" 3 "manual SR (rho =`S3_`sb_i'')") size(small) col(1) ring(100) position(12)  region(fcolor(white))   subtitle("`name_graph'")) ///
			xscale(r(0.53 .635)) xlabel(0.53(.02)0.63) ///
			yscale(r(0.6 1)) ylabel(0.6(.1)1) ///
			bgcolor(white) graphregion(color(white))
			graph save "$output/Figures/validation_share50_`sb_i'", replace
}
graph combine "$output/Figures/validation_share50_1" "$output/Figures/validation_share50_2" "$output/Figures/validation_share50_3", r(1) graphregion(color(white))   l1("Income share of the top 50 percent", size(small)) b1("HISCAM mass share of the top 50 percent", size(small)) imargin(zero)  
graph export "$output/Figures/validation_share50_combined.pdf" , replace 

*** Generate top-share correlation figure (Figure 8)

set more off

*** Load dataset with shares
*** Merge all data
use "$temp/income_1880.dta", clear
merge 1:1 id using "$temp/pop_1880.dta", nogenerate 
merge 1:1 id using "$temp/top_shares_BERLIN.dta", nogenerate 
forval hiscam_i = 1/3 {
	forval sb_i = 1/3 	{
		foreach stat in "count" "mean" {
			merge 1:1 id using "$temp/ab_1880_collapsed_`stat'_`hiscam_i'_`sb_i'.dta", nogenerate
		}
		
		forval share_i = 30/99  {
			merge 1:1 id using "$temp/hiscam_topshare_`hiscam_i'_`sb_i'_s`share_i'", nogenerate
			
		}
 		
	}
	
}


*** Compute correlations
forval sb_i = 1/3 {
	forvalues hiscam_i = 1/3 {
		forvalues topshare=30/99 {
			qui spearman top_share`topshare' hiscam_share_`hiscam_i'_`sb_i'_`topshare'
			qui gen rho`sb_i'_`hiscam_i'_`topshare' = r(rho)
			}
		}
	}

keep rho*
keep if _n==1
gen id=1

reshape long rho1_1_ rho1_2_ rho1_3_ rho2_1_ rho2_2_ rho2_3_ rho3_1_ rho3_2_ rho3_3_  , i(id) j(topshare)
 
*** Plot tract-level shares correlation (Figure 8)
forval sb_i = 1/3 {

*** Graph titles
		 
	if "`sb_i'"=="1" {
		local name_graph  "Automatic GR and..."
		}		
	if "`sb_i'"=="2" {
		local name_graph  "Semi-automatic GR and..."
		}
	if "`sb_i'"=="3" {
		local name_graph  "Manual GR and..."
		}
		 
	  twoway (scatter rho`sb_i'_1_ topshare , color(gray) msymbol(X)) (scatter rho`sb_i'_2_ topshare , color(gray) msymbol(Oh)) (scatter rho`sb_i'_3_ topshare , color(black) msymbol(Oh)), ///
			legend(order(1 "automatic SR" 2 "semi-automatic SR" 3 "manual SR") size(small) col(1) ring(100) position(12)  region(fcolor(white))   subtitle("`name_graph'")) ///
			xscale (r(29 102)) xlabel(30(10)99) xtitle("")   ///
			yscale(r(-1 1)) ylabel(-1(0.2)1, angle(horizontal) format(%3.1f))  ytitle("") ///
			bgcolor(white) graphregion(color(white))
			graph save "$output/Figures/topshares_correlation_`sb_i'", replace
}
graph combine "$output/Figures/topshares_correlation_1" "$output/Figures/topshares_correlation_2" "$output/Figures/topshares_correlation_3", r(1) graphregion(color(white))   l1("Correlation Income-HISCAM top-shares", size(small)) b1("Share held above quantile q", size(small)) imargin(zero)  
graph export "$output/Figures/topshares_correlation_combined.pdf" , replace 
