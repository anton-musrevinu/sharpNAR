SddWmc wmc(SddNode* sdd, const SddWmc* weights, const SddWmc* negweights, const SddLiteral var_count, SddManager* manager);
double sdd_query(SddNode* model, const SddWmc* weights, SddNode* query, const SddLiteral var_count, SddManager* manager, int* evidence, int evidencec);
SddWmc wmc_deri(SddLiteral lit, SddNode* sdd, const SddWmc* weights, const SddWmc* negweights, const SddLiteral var_count, SddManager* manager);
