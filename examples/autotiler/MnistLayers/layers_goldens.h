//
// Created by carol on 5/27/24.
//

#ifndef GAP_SDK_LAYERS_GOLDENS_H
#define GAP_SDK_LAYERS_GOLDENS_H



#if LAYER_TO_TEST == 0
int16_t golden_layer_0[] = {

};
int16_t *golden = golden_layer_0;

#elif LAYER_TO_TEST == 1
int16_t golden_layer_1[] = {

};
golden = golden_layer_1;

#elif LAYER_TO_TEST == 2

int16_t golden_layer_2[] = {

};
golden = golden_layer_2;
#else
#error "Not valid LAYER_TO_TEST"
#endif


#endif //GAP_SDK_LAYERS_GOLDENS_H
