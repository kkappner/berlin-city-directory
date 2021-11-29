// Set your working directory here
 cd "$githubfolder/gpinter/inst/stata"

// If necessary, specify where R is installed on your computer. You only need
// to do it if the program cannot find R by default. On Linux and macOS, you
// should find it at the addresses "/usr/bin/r" or "/usr/local/bin/r". On
// Windows, you should locate the file "Rterm.exe".
// Type "help rsource" for more details.

global Rterm_path `"$rsuitefolder"'

*if "${user}"=="Thilo_HOME" {

*global Rterm_path `"/Library/Frameworks/R.framework/Versions/3.6/Resources/bin/R"'
 
*}
// -------------------------------------------------------------------------- //
// Import tabulation example (US labor income, 2010)
// -------------------------------------------------------------------------- //

 

 /*

input	average			p		threshold	bracketavg
average	p	threshold	bracketavg

.			.9349697	6000	11904.929
.			.96621029	20000	31950.087
.			.98016119	52000	71916.562
 

end

input average     p  threshold  bracketavg
	12579.041	.90219132	6000	11904.929
	.			.9349697	20000	31950.087
	.			.96621029	52000	71916.562
	.			.98016119	100000	464982.48
end

  */
// -------------------------------------------------------------------------- //
// Save the tabulation as a Stata file
// -------------------------------------------------------------------------- //

// Using "saveold" is a useful precaution to make sure R will be able to read
// the file even if have a very recent version of Stata
saveold "tabulation-input.dta", version(11) replace

// -------------------------------------------------------------------------- //
// Call R from Stata and run the interpolation in it
// -------------------------------------------------------------------------- //

rsource, terminator(END_OF_R) roptions(--vanilla)

	// 'haven' is a R package for importing Stata '.dta' file
	library(haven)

	// 'gpinter' is the R package to perform generalized Pareto interpolation
	library(gpinter)

	// Import the Stata data into R
	data <- read_dta("tabulation-input.dta")

	// Perform interpolation
	distribution <- tabulation_fit(
		p = data$p,
		thr = data$threshold,
		bracketavg = data$bracketavg,
		average = data$average[1]
	)

	// Percentiles to include in the output
	percentiles_output <- c(
		seq(0, 0.99, 0.01), // Every percentile
		seq(0.991, 0.999, 0.001), // Every 1/10 of a percentile in top 1%
		seq(0.9991, 0.9999, 0.0001), // Every 1/100 of a percentile in top 0.1%
		seq(0.99991, 0.99999, 0.00001) // Every 1/1000 of a percentile in top 0.01%
	)

	// Create a tabulation for these detailed percentiles
	tabulation <- generate_tabulation(distribution, percentiles_output)

	// You may only keep the columns you are interested in by removing one of
	// these rows. You can also rename the columns by changing the names on the
	// left of the equal sign.
	tabulation <- data.frame(
		p               = tabulation$fractile,
		threshold       = tabulation$threshold,
		top_share       = tabulation$top_share,
		bottom_share    = tabulation$bottom_share,
		bracket_share   = tabulation$bracket_share,
		top_average     = tabulation$top_average,
		bottom_average  = tabulation$bottom_average,
		bracket_average = tabulation$bracket_average,
		invpareto       = tabulation$invpareto
	)

	// Export the detailed tabulation
	write_dta(tabulation, "tabulation-output.dta")

END_OF_R

// -------------------------------------------------------------------------- //
// Import the results of the R program in Stata
// -------------------------------------------------------------------------- //

use "tabulation-output.dta", clear
