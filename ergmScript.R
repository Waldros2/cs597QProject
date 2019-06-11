require('statnet')
require('yaml')

yaml_file = Sys.getenv("YAML")
yaml_data = yaml.load_file(yaml_file)
outfile <- paste0(yaml_data$elastic_search$save_path, yaml_data$ergm$outfile)

##############################################
# ESTABLISH DATA FRAME
##############################################
values     <- data.frame(date = as.Date(character())
                     , sum = numeric()
                     , atleast = numeric()
                     , stringsAsFactors = FALSE)

##############################################
# FUNCTIONS
##############################################
runErgm <- function(){
  
  currErgmModel <- ergm(networkDay~sum + atleast(threshold = yaml_data$ergm$threshold)
                    , response = 'aggregation'
                    , reference = ~Geometric
                    , control = control.ergm(
                         MCMLE.maxit = yaml_data$ergm$max_iterations
											 , MCMC.interval = yaml_data$ergm$interval
											 , MCMC.burnin = yaml_data$ergm$burnin
											 , MCMC.samplesize = yaml_data$ergm$sample_size
											 , parallel = yaml_data$ergm$threads)
					          , eval.loglik = FALSE)
  return (currErgmModel)
}
##############################################
# MODEL WORK
##############################################

date <- as.Date(yaml_data$elastic_search$start_date, format='%Y.%m.%d')
endDate <- as.Date(yaml_data$elastic_search$end_date, format='%Y.%m.%d')
while (date <= endDate)
{
  	ergmModel <- NULL
  	edgeList  <- NULL
  	
  	edgeListFile <- paste0(yaml_data$elastic_search$save_path
	  						, yaml_data$elastic_search$search_type
	  						, '_logstash-'
							  , format(date, "%Y.%m.%d.csv"))
  	
	try(edgeList <- read.csv(file = edgeListFile
							 , header = TRUE))
  	
	if(!is.null(edgeList))
  {
		networkDay 	<- network(mbFile
								, matrix.type = 'edgelist'
								, directed = TRUE
								, ignore.eval = FALSE
								, names.eval = 'aggregation')
  		
  		# Rerun the ERGM model until it converges
		try(ergmModel <- runErgm())
		  
		  # Parse ERGM model data to write to CSV
  		if(!is.null(ergmModel))
		  {
    		currValue <- data.frame(Date=as.character(date)
									, sum = ergmModel$coef[1]
									, atleast = ergmModel$coef[2])
    		
			  values <- rbind(values, currValue) 
  		  write.csv(values, file = outfile)
  		}
		  else
		  {
		    print(paste0("Could not calculate ERGM terms for ", date))
		  }
	}
  else
  {
    print(paste0("Could not find edgelist for ", date))
  }
  date <- date + 1
}