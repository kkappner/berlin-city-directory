*** PREPARE TOP-INCOMES DATA FOR FIGURES 7 AND 8
*** Run this file to prepare the data for Figures 7 and 8.
*** You need a working R installation with gpinter, and the rsource Stata package.

set more off
 
 
*** Import average incomes
import excel "$rawdata/validation_berlin_ab1880/Incomes_1880_revised", clear first
duplicates report id 
save "$temp/income_1880.dta", replace
		
*** Import tax data by district 
import excel "$rawdata/validation_berlin_ab1880/Classified_Income_Data_Consolidated.xlsx", clear sheet("Raw") first

	* Remerge 72, 76, 111, and 184
	
				replace id=721 if id==722
				replace id=761 if id==762
	
				replace id=1111 if id==1112
				replace id=1841 if id==1842
			
				collapse (sum) N_people N_people_income_tax tax_exempt_under_cutoff tax_exempt_young tax_exempt_military tax_exempt_low_income2 tax_class_1 tax_class_2 tax_class_3 tax_class_4 tax_class_5 tax_class_6 tax_class_7 tax_class_8 tax_class_9 tax_class_10 tax_class_11 tax_class_12 total_tax T, by(id)
		
				replace id=72  if id==721
				replace id=76  if id==761
				replace id=111 if id==1111
				replace id=184 if id==1841
	
	*** Merge with average axes 
	merge 1:1 id using "$temp/income_1880.dta"
	
	*** Drop empty entries and the castle entry
	drop if _merge!=3
		
*** Use total income estimate by city officials (deviates 1% from what they describe in the sources -> potentially because we now exclude King's income and Fortschreibung
gen Income_Bezirk=N_people*income

				/*		
				*** Check accuracy
				egen sum_totalincome=sum(Income_Bezirk)
							format sum_totalincome %9.0f		
				*/

		
*** Generate tax units (we want a hosehold/tax unit level dataset => need to transform exempted and income tax payers in to households (instead of household heads and their relatives)
egen N_people_exempted=rowtotal(tax_exempt_under_cutoff tax_exempt_young tax_exempt_military tax_exempt_low_income2)
egen N_taxunits_klassensteuer=rowtotal(tax_class_1 tax_class_2 tax_class_3 tax_class_4 tax_class_5 tax_class_6 tax_class_7 tax_class_8 tax_class_9 tax_class_10 tax_class_11 tax_class_12)

gen N_people_klassensteuer=N_people-N_people_income_tax-N_people_exempted

gen R_ppl_household_klassensteuer=N_people_klassensteuer/N_taxunits_klassensteuer

**** Assume same household size of exempted as for those paying Klassensteuer
gen N_taxunits_exempted=N_people_exempted/R_ppl_household_klassensteuer

**** Generate income tax payers assuming city-wide ratio of tax units to tax+family (for income taxpayers)
gen N_taxunits_income=N_people_income_tax*(25200/82062)
					
		 
*** Check city wide totals of population/N tax units with  source (Accuracy is high) 
				{/*
						egen N_people_total =sum(N_people) 
										* 200 people difference /~100 households
								
						egen N_people_klassensteuer_total=sum(N_people_klassensteuer)
										* 139 people difference   
				 
						
						egen total_taxpayer_income=sum(N_people_income_tax)
										* 0 people difference
						
						egen N_people_exempted_total=sum(N_people_exempted)
										* 13 people difference  

										
						forvalues r=1/12{
								egen N_taxpayer_classsteuer_`r'=sum(tax_class_`r')
						}
										* Grand totals for each class - only minor deviations
										
*/
}
						
*** The respective estimates of the income in a given bracket are given by the source
gen Inc_TU_klassensteuer=480*tax_class_1+720*tax_class_2+1020*tax_class_3+1170*tax_class_4+1320*tax_class_5+1470*tax_class_6+1620*tax_class_7+1770*tax_class_8+1920*tax_class_9+2220*tax_class_10+2520*tax_class_11+2820*tax_class_12
				
*egen dc_N_klassensteuer=sum(number_taxpayers_klassensteuer) /// Very good match
									
gen INC_TU_exempted=N_taxunits_exempted*150 

gen INC_TU_incometax=Income_Bezirk- Inc_TU_klassensteuer -INC_TU_exempted

*** Set estimated income of income taxpayers to 0 if there are none (4 cases)
replace INC_TU_incometax=0 if N_taxunits_income==0

replace Income_Bezirk=INC_TU_incometax+Inc_TU_klassensteuer+INC_TU_exempted

gen Inc_avg_TU_all= Income_Bezirk/( N_taxunits_exempted+N_taxunits_klassensteuer+N_taxunits_income)

*** check plausibility => Average income always higher for those paying income tax than for average 
				 { 
						/*
						
						gen Inc_avg_TU_incometaxpayers=INC_TU_incometax/N_taxunits_income
						
						sort Inc_avg_TU_incometaxpayers
						
						sort id 
						order id N_people_klassensteuer
						*/
						}
		
*** Prepare data for Pareto: needed: a) average income		
forvalues r=1/12{
	rename tax_class_`r' i_`r'
	}

gen i_13=N_taxunits_income

*** Lower boundary 
gen s_i_1= 	420
gen s_i_2=	660				
gen s_i_3=	900				
gen s_i_4=	1050			
gen s_i_5=	1200			
gen s_i_6=	1350			
gen s_i_7=	1500			
gen s_i_8=	1650			
gen s_i_9=	1800			
gen s_i_10=	2100			
gen s_i_11=	2400			
gen s_i_12=	2700			
gen s_i_13=	3000			

gen w_1= 480*i_1
gen w_2= 720*i_2
gen w_3= 1020*i_3
gen w_4= 1170*i_4
gen w_5= 1320*i_5
gen w_6= 1470*i_6
gen w_7= 1620*i_7
gen w_8= 1770*i_8
gen w_9= 1920*i_9
gen w_10= 2220*i_10
gen w_11= 2520*i_11
gen w_12= 2820*i_12
gen w_13= INC_TU_incometax

gen indi_total=N_taxunits_exempted+N_taxunits_klassensteuer+N_taxunits_income
rename Income_Bezirk Income_total
gen Territory="Berlin"

*** Save data
keep id i_1 i_2 i_3 i_4 i_5 i_6 i_7 i_8 i_9 i_10 i_11 i_12 i_13 s_i_1 s_i_2 s_i_3 s_i_4 s_i_5 s_i_6 s_i_7 s_i_8 s_i_9 s_i_10 s_i_11 s_i_12 s_i_13 w_1 w_2 w_3 w_4 w_5 w_6 w_7 w_8 w_9 w_10 w_11 w_12 w_13 indi_total  Wealth_total
save "$temp/classfied_tax_data", replace
				
*** Do gpinter for top-1 share  
levelsof id, local(BEZIRK)
foreach B of local BEZIRK{
	use "$temp/classfied_tax_data", clear
	keep if id==`B'

	order indi_total  Income_total

	*** Generate percentiles
	unab vars : i_*
	gen n_brackets=13

	*** Check whether x is only folowed by a number
		local check : subinstr local vars "i_" "", all
		local check : subinstr local check " " "", all
		confirm number `check'

		local k : word count `vars'
		ds
		local allvars "`r(varlist)'"
		local order : list allvars - vars
		forvalues i = `k'(-1)1 {
			local order "`order' i_`i'"
		}
		order `order'

	sum n_brackets
	local brackets=r(max)
			
	forvalues i=1/`brackets'{
		gen average_`i'=w_`i'/i_`i'
		egen cum_i_`i'=rowtotal(i_`brackets'-i_`i') 
		gen p_`i'=1-(cum_i_`i'/indi_total)
	}
		
	reshape long p_ average_ w_ s_i_  i_     , i(id) j(bracket)   
	
	drop if average_==.
	
	rename average bracketavg
	
	gen average=Income_total/indi_total
	
	rename s_i threshold 
	rename p_ p
	
	order average p  threshold bracketavg
	
	keep average p  threshold bracketavg
	
	replace average=. if _n!=1
		
			 
	*** Test whether the thresholds align with bracket averages
	gen upper_bound=threshold[_n+1]
	gen next_bracket=bracketavg[_n+1]
	
	gen error= 0 if bracketavg>threshold & bracketavg<upper_bound
	
	replace error=1 if error==.
	 
	egen error_all=sum(error)
	
	if error_all!=0{
		di `l'
		di "the thresholds and the bracket averages are inconsistent"
		ERROR
		}
					
	drop upper_bound-error_all
																				
	*** Run pareto interpolation using gpinter
	
	do "$scripts/AuxDo/_TA_run_paretoinR" 
 
	keep if p>.29  & p<=.99
	
	keep top_share p
	
	gen id=`B'
	replace p=p*100
	 
	replace p=round(p)

	reshape wide top_share, i(id) j(p)
	
	save "$temp/topshares_`B'" , replace
	
	}

levelsof id, local(BEZIRK)
clear

foreach B of local BEZIRK{
	append using "$temp/topshares_`B'"
	}

save "$temp/top_shares_BERLIN", replace 
