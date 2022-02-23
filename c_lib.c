
#include "stdint.h"
#include "stdbool.h"

static inline uint8_t qMin(uint8_t a, uint8_t b)
{
    return a > b ? b : a;
}

static inline uint8_t qMax(uint8_t a, uint8_t b)
{
    return a > b ? a : b;
}

bool lab_threshold(uint8_t* l, uint8_t* a, uint8_t* b, uint8_t* out, uint32_t w, uint32_t h, uint8_t* thresholds, bool invert )
{

    for(int y = 0; y < h; y++)
    {
        for(int x = 0; x < w; x++)
        {
            int offset = y*w + x;
            bool LMinOk = l[offset] >= qMin(thresholds[0], thresholds[1]);
            bool LMaxOk = l[offset] <= qMax(thresholds[0], thresholds[1]);
            bool AMinOk = a[offset] >= qMin(thresholds[2], thresholds[3]);
            bool AMaxOk = a[offset] <= qMax(thresholds[2], thresholds[3]);
            bool BMinOk = b[offset] >= qMin(thresholds[4], thresholds[5]);
            bool BMaxOk = b[offset] <= qMax(thresholds[4], thresholds[5]);
            bool allOk = (LMinOk && LMaxOk && AMinOk && AMaxOk && BMinOk && BMaxOk) ^ invert;
            out[offset] =  allOk ? 255 : 0;
        }
    }
    return true;
}

