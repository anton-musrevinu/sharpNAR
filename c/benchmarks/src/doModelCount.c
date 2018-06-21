#include <stdio.h>
#include <stdlib.h>
#include "sddapi.h"
#include <math.h>
#include <sys/time.h>
#include <string.h>


SddWmc mc(SddNode* sdd, SddManager* manager);
char* getfield(char* line, int num);
void remove_all_chars(char* str, char* c);

SddWmc mc(SddNode* sdd, SddManager* manager){

  int log_mode = 1;
  
  WmcManager* wmc_manager = wmc_manager_new(sdd, log_mode, manager);
  
  SddWmc modelcount = wmc_propagate(wmc_manager);
  
  wmc_manager_free(wmc_manager);
  long double count = modelcount;
  // if (log_mode != 0)
  //   count = exp(count);
  return count;
}

char* getfield(char* line, int num)
{
    char* tok;
    for (tok = strtok(line, ",");
            tok && *tok;
            tok = strtok(NULL, ",\n"))
    {
        if (!--num)
            return tok;
    }
    return NULL;
}

void remove_all_chars(char* str, char* c) {
    char *pr = str, *pw = str;
    while (*pr) {
        *pw = *pr++;
        pw += (strcmp(pw,c) != 0);
    }
    *pw = '\0';
}


int main(int argc, char** argv) {


  //char file[] = "APPROXWMI/1023_data";
  int verbose = 0;
  if (argc == 2){
    if (strcmp(argv[1],"-v") == 0)
      verbose = 1;
  }
  printf("After reading args verbose = %d\n",verbose);
  char path[] = "./../../mcbenchmarks/sdd/";

  char inputfile[] = "./../../mcbenchmarks/algorithms_specs/enumeration_input.csv";

  FILE* stream = fopen(inputfile, "r");
  FILE *f = fopen("./output/benchmark_ALGORITHM_MC_UCLA.log", "w");

  char line[1024];

  while (fgets(line, 1024, stream) != NULL)
  {
      char* tmp = strdup(line);
      if (strncmp(tmp, "#'", 1) == 0)
        continue;
      remove_all_chars(tmp,"\n");
      char* file = getfield(tmp,1);
      //printf("Starting Model Counting on: %s\n", file);
      
      char* vtreeFileName = malloc(strlen(file) + strlen(path) + strlen(".vtree") + 1);
      char* sddFileName = malloc(strlen(file) + strlen(path) + strlen(".sdd") + 1);
      sprintf(vtreeFileName, "%s%s.vtree", path, file);
      sprintf(sddFileName, "%s%s.sdd", path, file);

      //printf("VTREEMANAGER: %s, SddManager: %s\n\n",vtreeFileName,sddFileName);

      //Set Up Vtree;
      Vtree* vtree = sdd_vtree_read(vtreeFileName);

      //Set up Manager
      SddManager* manager = sdd_manager_new(vtree);

      //Read SDD
      SddNode* alpha = sdd_read(sddFileName, manager);

      int size = sdd_size(alpha);
      int sizeTotal = sdd_manager_size(manager);
      int nodeCount = sdd_count(alpha);
      int varCount = sdd_manager_var_count(manager);

      //printf("  sdd size     = %d\n", sddsize);
      //printf("  sdd varCount = %d\n", varCount);

      //clock_t start = clock();
      struct timeval tv1, tv2;
      gettimeofday(&tv1, NULL);
      long double modelCount  = mc(alpha,manager);
      gettimeofday(&tv2, NULL);
      long double modelCountTime = (double) (tv2.tv_usec - tv1.tv_usec) / 1000000 + (double) (tv2.tv_sec - tv1.tv_sec);
      //clock_t end = clock();
      //double modelCountTime = (float)(end - start) / CLOCKS_PER_SEC;

      //printf("ModelCount: %f in %f seconds \n",modelCount,modelCountTime);
      if(verbose == 1)
        printf("MC,UCLA,#threads:  %d,%s,%d\t,%d\t,%d\t,%d\t,%f\t,%Lf\n",1,file,sizeTotal,size,nodeCount,varCount,modelCountTime,modelCount);
      fprintf(f,"MC,UCLA,#threads: %d,%s,%d\t,%d\t,%d\t,%d\t,%f\t,%Lf\n",1,file,sizeTotal,size,nodeCount,varCount,modelCountTime,modelCount);
      //////// CLEAN UP //////////

      sdd_manager_free(manager);

      free(tmp);
  }



  return 0;
}
