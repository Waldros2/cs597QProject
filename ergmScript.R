burnin     <- 20000000   # BURNIN      = 20000000
maxit      <- 1000       # MAXIT       = 1000
samplesize <- 10000      # SAMPLESIZE  = 10000
interval   <- 3000       # INTERVAL    = 3000
##############################################
# OPTIONS FOR VALUES

values     <- data.frame(date = as.Date(character())
                     , sum = numeric()
                     , nonzero = numeric()
                     , atLeastMedian = numeric()
                     , atLeastMean = numeric()
                     , stringsAsFactors = FALSE)

##############################################
# FUNCTIONS
##############################################
runErgm <- function(){
  
  currErgmModel <- ergm(networkDay~sum + edges + atleast(threshold = median) + atleast(threshold = mean)
                    , response = 'MB'
                    , reference = ~Geometric
                    , control = control.ergm(
                         MCMLE.maxit = maxit
                       , MCMLE.density.guard = exp(4)
											 , MCMC.interval = interval
											 , MCMC.burnin = burnin
											 , MCMC.samplesize = samplesize
											 , parallel = 4)
					          , eval.loglik = FALSE)
  return (currErgmModel)
}
##############################################
# MODEL WORK
##############################################
baseline <- '/home/scott/Documents/networkresearch/data/dns/baseline.csv'
baseline <- read.csv(file = baseline, header = TRUE, row.names = 1)

date <- as.Date('2018.04.17', format='%Y.%m.%d')
endDate <- as.Date('2018.05.12', format='%Y.%m.%d')
while (date <= endDate)
{
  	ergmModel <- NULL
  	edgeList  <- NULL
    dayOfWeek <- weekdays(date)
    
  	edgeListFile <- paste0('/home/scott/Documents/networkresearch/data/dns/logstash-'
							 , format(date, "%Y.%m.%d.csv"))
  	
	try(edgeList <- read.csv(file = edgeListFile
							 , header = TRUE))
  	
	if(!is.null(edgeList))
  {
		networkDay 	<- network(mbFile
								, matrix.type = 'edgelist'
								, directed = TRUE
								, ignore.eval = FALSE
								, names.eval = 'MB')

  		median 	<- median(networkDay %e% 'MB')
  		mean 		<- mean(networkDay %e% 'MB')
  		
  		# Rerun the ERGM model until it converges
		  attempt 	<- 0
  		while(is.null(ergmModel) && attempt < 5)
		  {
			  try(ergmModel <- runErgm())
    		  attempt <- attempt + 1
  		}
		  
		  # Parse ERGM model data to write to CSV
  		if(!is.null(ergmModel))
		  {
    		currValue <- data.frame(Date=as.character(date)
									, Sum = ergmModel$coef[1]
									, edges = ergmModel$coef[2]
									, atLeastMedian = ergmModel$coef[3]
									, atLeastMean = ergmModel$coef[4])
    		
			  values <- rbind(values, currValue) 
  		  write.csv(values, file = '/home/waldros2/CSCI-WWU/networkresearch/data/values2.csv')
  		  
  		  # Update baseline values
  		  baseline[dayOfWeek, 'Median'] <- median(networkDay %e% 'Connections')
  		  baseline[dayOfWeek, 'Mean'] <- mean(networkDay %e% 'Connections')
  		}
	}
  date <- date + 1
}

################################################
# Extra
################################################

mbFile <- read.csv(file = '/home/scott/Documents/networkresearch/data/byte/byte_logstash-2018.04.30.csv', header = TRUE)

