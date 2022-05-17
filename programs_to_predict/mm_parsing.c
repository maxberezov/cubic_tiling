

int main(int argc, const char* argv[])
{

int i,j,k,l;

for ( i = 0; i < 1024; i++)
for ( j = 0; j < 1024; j++)
loop_1: for ( k = 0; k < 1024; k++)
{
C[i][j] = C[i][j] + A[i][k] * B[k][j];
}

return 0;
}
