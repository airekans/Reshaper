#include "move_file_helper_test.h"
#include "no_source_header.h"

int main()
{
    IndirectlyInclude* pII = new IndirectlyInclude(1);
    NoSourceHeader noSour;
    noSour.SetIndirectly(pII);
    delete pII;

    MoveFileHelperTest mfht;
    return 0;
}
