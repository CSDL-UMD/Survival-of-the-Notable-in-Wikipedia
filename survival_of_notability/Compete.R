#======== Experiment with our data =======

options(repos=c(CRAN = "https://cloud.r-project.org/"))
install.packages(c("survival","tidyverse","dplyr","ggplot2","arm","modelsummary","broom"))

library(survival)
library(broom)
library(tidyverse)
library(dotwhisker)
library(dplyr)
library(ggplot2)
library(arm)           # coefplot()
library(modelsummary)  # modelplot()
library(ggstats)


df_all = data.frame()
yy <- 2005

for (xxx in 2:20){
  file_name <- paste("data/interim/iter_", as.character(xxx),".csv",sep = "")
  print(file_name)  
  data3 <- read.csv(file_name, )
  
  print(yy,xxx)
  
  event <-data3$event2
  data3$event2 <- factor(event,0:6,levels=c("not-nominated","nominated","delete","keep","redirect","merge","other"))
  data3<-data3[data3$event2 %in% c(0,1,2,3,4,5),]
  
  year <- as.character(yy)
  
  mfit3 <- coxph(Surv(tstart, tstop, event2) ~ unlist(Gender) + unlist(Status) +unlist(Gender)*unlist(Status), data=data3, id=id, control = coxph.control(timefix = FALSE))
  print(mfit3$transitions)

  fit1_results <- tidy(mfit3) %>% 
    mutate(year = year)
  
  fit1_results <- fit1_results %>%
    mutate(term = str_replace_all(term, c("_1:2"="_Nominated","_2:3" = "_Delete", "_2:4" = "_Keep","_2:5" = "_Redirect","_2:6" = "_Merge","_1:3"="_remove","_1:4"="_remove","_1:5"="_remove","_1:6"="_remove","_1:7"="_remove", "unlist(Status)"="","unlist"="","Status"="","\\(" = "","\\)"="")))
  
  # Split the "term" column by the underscore
  split_term <- strsplit(as.character(fit1_results$term), "_")
  
  # Convert the result into a data frame with two new columns
  fit1_results <- data.frame(fit1_results, 
                          covariate = sapply(split_term, "[", 1),
                          action = sapply(split_term, "[", 2))
  
  # View the new columns
  print(fit1_results)
  df_all <- rbind(df_all,fit1_results)
  yy <- yy + 1
  
}


write.csv(df_all, "data/processed/data_for_compete_risk_all_iter_all_results3.csv")







