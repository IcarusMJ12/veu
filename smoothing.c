#line 2 "smoothing.c"
unsigned char counter[4][4];
int match_i, is_zero, is_match, di, di_max, dj_max, dj_initial;

//iterate over the matrix 's'
for(int i=0;i<x;i++)
{
	for(int j=0;j<y;j++)
	{
		//zero out the counter for each pixel in the image
		for(int ci=0;ci<4;ci++)
		{
			for(int cj=0;cj<3;cj++)
				counter[ci][cj]=255;
			counter[ci][3]=0;
		}
		di=i-r;
		if(di<0)
			di=0;
		dj_initial=j-r;
		if(dj_initial<0)
			dj_initial=0;
		di_max=i+r+1;
		if(di_max>x)
			di_max=x;
		dj_max=j+r+1;
		if(dj_max>y)
			dj_max=y;
		//iterate over a sliding window within the matrix
		for(;di<di_max;di++)
		{
			for(int dj=dj_initial;dj<dj_max;dj++)
			{
				//iterate over a list of potential matches
				for(match_i=0;match_i<4;match_i++)
				{
					//check if the next element is pure white, which means not initialized in our book
					is_zero=1;
					for(int cj=0;cj<3;cj++)
					{
						if(counter[match_i][cj]!=255)
						{
							is_zero=0;
							break;
						}
					}
					//if not zero, check if it matches existing color
					if(!is_zero)
					{
						for(int cj=0;cj<3;cj++)
						{
							is_match=1;
							if(counter[match_i][cj]!=s(di,dj,cj))
							{
								is_match=0;
								break;
							}
						}
						//if it does increment counter and continue with next pixel
						if(is_match)
						{
							counter[match_i][3]+=1;
							break;
						}
					}
					else
					{
						for(int cj=0;cj<3;cj++)
							counter[match_i][cj]=s(di,dj,cj);
						counter[match_i][3]=1;
						break;
					}
				}
			}
		}
		match_i=0;
		for(int ci=1;ci<4;ci++)
		{
			if(counter[ci][3]>counter[match_i][3])
				match_i=ci;
		}
		//if(counter[match_i][3]<5)
		for(int cj=0;cj<3;cj++)
		{
			d(i,j,cj)=counter[match_i][cj];
		}
		d(i,j,3)=255;
	}
}
