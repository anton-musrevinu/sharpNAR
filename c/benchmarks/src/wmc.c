#include "wmc.h"

double sdd_query(SddNode* model, const SddWmc* weights, SddNode* query, const SddLiteral var_count, SddManager* manager, int* evidence, int evidencec){
//   printf("conjoining model with query...\n");
  
  
  SddSize msize = sdd_size(model);
  
  int i = 0;
  while (i < evidencec){
    model = sdd_condition(evidence[i], model, manager);
    if(i == 0){sdd_save_as_dot("output/example3_model_0.dot",model);}
    if(i == 1){sdd_save_as_dot("output/example3_model_1.dot",model);}
    i++;
  }
  
  i = 0;
  while (i < evidencec){
    query = sdd_condition(evidence[i], query, manager);
    i++;
  }
  
  sdd_save_as_dot("output/example3_model.dot",model);
  sdd_save_as_dot("output/example3_query.dot",query);

  SddSize mesize = sdd_size(model);


  SddWmc* negweights = (SddWmc*)malloc(sizeof(SddWmc)*(var_count+1));
  negweights[1] = .5; //PhiA
  for(int i = 2; i <= var_count; i++){
    negweights[i] = 1;
  }

  SddWmc wmcModel = wmc(model, weights, negweights, var_count, manager);
  
  SddNode* queryModel = sdd_conjoin(model, query, manager);
  
//   printf("model and query conjoined\n");
  SddWmc wmcQueryModel = wmc(queryModel, weights, negweights, var_count, manager);
  printf("Computing prop: %f / %f)\n",wmcQueryModel, wmcModel);

  return wmcQueryModel/wmcModel;
}

double sdd_cond(SddNode* model, const SddWmc* weights, SddLiteral lit, const SddLiteral var_count, SddManager* manager, int* evidence, int evidencec){
//   printf("conjoining model with query...\n");
  
  
  SddSize msize = sdd_size(model);
  
  int i = 0;
  while (i < evidencec){
    model = sdd_condition(evidence[i], model, manager);
    i++;
  }

  SddSize mesize = sdd_size(model);


  SddWmc* negweights = (SddWmc*)malloc(sizeof(SddWmc)*(var_count+1));
  negweights[1] = .5; //PhiA
  for(int i = 2; i <= var_count; i++){
    negweights[i] = 1;
  }

  SddWmc wmcModel = wmc(model, weights, negweights, var_count, manager);
  SddWmc wmcQueryModel = wmc_deri(lit,model, weights, negweights, var_count, manager);
  printf("Computing prop: %f / %f)\n",wmcQueryModel, wmcModel);

  return wmcQueryModel/wmcModel;
}

SddWmc wmc(SddNode* sdd, const SddWmc* weights, const SddWmc* negweights, const SddLiteral var_count, SddManager* manager){  
  WmcManager* wmc_manager = wmc_manager_new(sdd, 0, manager);
  int i = 1;
  while (i<=var_count){
    wmc_set_literal_weight(i, weights[i], wmc_manager);
    i++;
  }
  
  
  if (NULL != negweights) {
    i = 1;
    while (i<=var_count){
      wmc_set_literal_weight(-i, negweights[i], wmc_manager);
      i++;
    }
  }
  
  SddWmc modelcount = wmc_propagate(wmc_manager);
  
  wmc_manager_free(wmc_manager);
  return modelcount;
}

SddWmc wmc_deri(SddLiteral lit, SddNode* sdd, const SddWmc* weights, const SddWmc* negweights, const SddLiteral var_count, SddManager* manager){  
  WmcManager* wmc_manager = wmc_manager_new(sdd, 0, manager);
  int i = 1;
  while (i<=var_count){
    wmc_set_literal_weight(i, weights[i], wmc_manager);
    i++;
  }
  
  
  if (NULL != negweights) {
    i = 1;
    while (i<=var_count){
      wmc_set_literal_weight(-i, negweights[i], wmc_manager);
      i++;
    }
  }
  
  SddWmc modelcount = wmc_literal_derivative(lit,wmc_manager);
  
  wmc_manager_free(wmc_manager);
  return modelcount;
}