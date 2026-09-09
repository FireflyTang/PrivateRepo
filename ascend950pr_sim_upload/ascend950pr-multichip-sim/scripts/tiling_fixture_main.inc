// Experimental small-case tiling. Included after host tiling functions.
#include <fstream>
#include <iostream>
int main(int argc,char**argv){
 MegaMoeTilingData t{};
 t.moeExpertPerRank=1;t.bs=16;t.h=1024;t.hiddenDim=512;t.epWorldSize=2;
 t.aicNum=2;t.blockAivNum=4;t.blockNumPerEP=1;t.maxOutputSize=32;t.topK=1;
 t.numMaxTokensPerRank=16;t.rankNumPerServer=2;t.clampLimit=std::numeric_limits<float>::max();
 t.activationAlpha=1.702f;t.activationBeta=1.f;t.mGroupsPerWave=optiling::CalcMGroupsPerWave(&t,t.aicNum);
 t.dispatchBufferConfig=optiling::CalcDispatchBufferConfig(&t,1,248*1024);
 t.combineSyncSlotCountPerExpert=optiling::CalcCombineSyncSlotCountPerExpert(&t);
 optiling::SetTopkValidIndexBufferConfigs(&t,1,248*1024);
 optiling::SetUnpermuteBufferConfigs(&t,ge::DT_BF16,248*1024);
 std::ofstream f(argv[1],std::ios::binary);f.write((char*)&t,sizeof(t));
 std::cout<<"tiling_size="<<sizeof(t)<<" workspace="<<WorkspaceLayout(&t).workspaceSize<<std::endl;
}
