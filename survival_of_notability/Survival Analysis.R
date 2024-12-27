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
library("stringr")




file_name <- paste("data/processed/data_for_compete_risk_all.csv",sep = "")
print(file_name)  
data1 <- read.csv(file_name, )
event <-data1$event
data1$event2 <- factor(event,0:6,levels=c("not-nominated","nominated","delete","keep","redirect","merge","other"))
data2<-data1[data1$event2 %in% c(0,1,2,3,4,5),]
data3<-data1[data1$event2 %in% c(2,3,4,5),]
data3$num_users<-scale(data3$num_users)
data3$num_messages<-scale(data3$num_messages)
data3$ave_num_words<-scale(data3$ave_num_words)

mfit0 <- coxph(Surv(tstart,tstop, event2) ~  unlist(Gender) + unlist(Status) + unlist(Gender)*unlist(Status), data=data2, id=id, control = coxph.control(timefix = FALSE))
print(mfit0$transitions)
mfit01 <- coxph(Surv(tstart,tstop, event2) ~  unlist(Gender) + unlist(Status), data=data2, id=id, control = coxph.control(timefix = FALSE))
print(mfit01$transitions)


mfit1 <- coxph(Surv(tstart,tstop, event2) ~  unlist(Gender) + unlist(Status) + unlist(num_users) + unlist(num_messages) + unlist(ave_num_words), data=data3, id=id, control = coxph.control(timefix = FALSE))
print(mfit1$transitions)

mfit2 <- coxph(Surv(tstart,tstop, event2) ~  unlist(Gender) + unlist(Status) + unlist(num_users) + unlist(num_messages) + unlist(ave_num_words) + unlist(Gender)*unlist(Status), data=data3, id=id, control = coxph.control(timefix = FALSE))
print(mfit2$transitions)

fit0_results <- tidy(mfit0, conf.int = TRUE) %>% 
  mutate(model = "Multi-state + Int. T")
fit0_results <- fit0_results %>%
  mutate(term = str_replace_all(term, c("_1:2"="_Nomination","_2:3" = "_Delete", "_2:4" = "_Keep","_2:5" = "_Redirect","_2:6" = "_Merge","_1:3"="_remove","_1:4"="_remove","_1:5"="_remove","_1:6"="_remove")))
fit0_results <- fit0_results[!fit0_results$term %in% c('unlist(Gender)_remove','unlist(Gender):unlist(Status)Contemporary Dead_remove','unlist(Gender):unlist(Status)Historical_remove','unlist(Status)Contemporary Dead_remove','unlist(Status)Historical_remove'),]

fit01_results <- tidy(mfit01, conf.int = TRUE) %>% 
  mutate(model = "Multi-state")
fit01_results <- fit01_results %>%
  mutate(term = str_replace_all(term, c("_1:2"="_Nomination","_2:3" = "_Delete", "_2:4" = "_Keep","_2:5" = "_Redirect","_2:6" = "_Merge","_1:3"="_remove","_1:4"="_remove","_1:5"="_remove","_1:6"="_remove")))
fit01_results <- fit01_results[!fit01_results$term %in% c('unlist(Gender)_remove','unlist(Gender):unlist(Status)Contemporary Dead_remove','unlist(Gender):unlist(Status)Historical_remove','unlist(Status)Contemporary Dead_remove','unlist(Status)Historical_remove'),]


fit1_results <- tidy(mfit1, conf.int = TRUE) %>% 
  mutate(model = "Single-state")
fit1_results <- fit1_results %>%
  mutate(term = str_replace_all(term, c("_1:3" = "_Delete", "_1:4" = "_Keep","_1:5" = "_Redirect","_1:6" = "_Merge","_1:7"="_remove")))
fit1_results <- fit1_results[!fit1_results$term %in% c('unlist(Gender)_remove','unlist(Gender):unlist(Status)Contemporary Dead_remove','unlist(Gender):unlist(Status)Historical_remove','unlist(Status)Contemporary Dead_remove','unlist(Status)Historical_remove','unlist(num_users)_remove','unlist(num_messages)_remove','unlist(ave_num_words)_remove'),]


fit2_results <- tidy(mfit2, conf.int = TRUE) %>% 
  mutate(model = "Single-state + Int.T")
fit2_results <- fit2_results %>%
  mutate(term = str_replace_all(term, c("_1:3" = "_Delete", "_1:4" = "_Keep","_1:5" = "_Redirect","_1:6" = "_Merge","_1:7"="_remove")))
fit2_results <- fit2_results[!fit2_results$term %in% c('unlist(Gender)_remove','unlist(Gender):unlist(Status)Contemporary Dead_remove','unlist(Gender):unlist(Status)Historical_remove','unlist(Status)Contemporary Dead_remove','unlist(Status)Historical_remove','unlist(num_users)_remove','unlist(num_messages)_remove','unlist(ave_num_words)_remove'),]

print("Bind All")

model_results_all <- bind_rows(fit01_results,fit0_results,fit1_results,fit2_results)
model_results_all <- model_results_all %>%
  mutate(term = str_replace_all(term, c("Nomination"="Nominate","Historical"="Hist.","Contemporary Dead"="Cont. Dead","unlist"="","Status"="","\\(" = "","\\)"="")))

level_order_all <- c('ave_num_words_Merge','ave_num_words_Redirect','ave_num_words_Keep','ave_num_words_Delete','num_messages_Merge', 'num_messages_Redirect','num_messages_Keep','num_messages_Delete','num_users_Merge','num_users_Redirect','num_users_Keep','num_users_Delete','ave_num_words_Merge','ave_num_words_Redirect','ave_num_words_Keep','ave_num_words_Delete','num_messages_Merge', 'num_messages_Redirect','num_messages_Keep','num_messages_Delete','num_users_Merge','num_users_Redirect','num_users_Keep','num_users_Delete',"Gender:Hist._Merge","Gender:Hist._Redirect","Gender:Hist._Keep","Gender:Hist._Delete","Gender:Hist._Nominate","Gender:Hist._Merge","Gender:Hist._Redirect","Gender:Hist._Keep","Gender:Hist._Delete","Gender:Hist._Nominate","Gender:Cont. Dead_Merge","Gender:Cont. Dead_Redirect","Gender:Cont. Dead_Keep","Gender:Cont. Dead_Delete","Gender:Cont. Dead_Nominate","Gender:Cont. Dead_Merge","Gender:Cont. Dead_Redirect","Gender:Cont. Dead_Keep","Gender:Cont. Dead_Delete","Gender:Cont. Dead_Nominate",'Hist._Merge','Hist._Redirect','Hist._Keep','Hist._Delete','Hist._Nominate','Cont. Dead_Merge','Cont. Dead_Redirect','Cont. Dead_Keep','Cont. Dead_Delete','Cont. Dead_Nominate', 'Gender_Merge','Gender_Redirect','Gender_Keep','Gender_Delete','Gender_Nominate')

all_model_p <- ggplot(data = model_results_all, 
       aes(x = estimate, y = term, xmin = conf.low, xmax = conf.high, 
           color = model, shape = model)) +
  geom_pointrange() +
  geom_vline(xintercept = 0)+
  labs(
    x = "Coefficient Estimate",
    y = "Predictor") +
  scale_y_discrete(limit=level_order_all) 
  #ggpubr::theme_pubclean(flip = TRUE)
 
 ggsave('reports/figures/Fig5-All_models.pdf', plot= all_model_p)