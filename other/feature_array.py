#import matplotlib.pyplot as plt
import descarteslabs as dl
import numpy as np
import math
import sys
from sys import exit
import sklearn
from sklearn import svm
import time
from sklearn.preprocessing import StandardScaler
from celery import Celery

####################
# Function         #
####################
### Running mean/Moving average
def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')
    
def variance(x):   
    '''function to compute the variance (std dev squared)'''
    xAvg=np.mean(x)
    xOut=0.
    for k in range(len(x)):
        xOut=xOut+(x[k]-xAvg)**2
    xOut=xOut/(k+1)
    return xOut

def rolling_median(var,window):
    '''var: array-like. One dimension
    window: Must be odd'''
    n=len(var)
    halfW=int(window/2)
    med=np.zeros(shape=(var.shape))
    for j in range(halfW,n-halfW):
        med[j]=np.ma.median(var[j-halfW:j+halfW+1])
     
    for j in range(0,halfW):
        w=2*j+1
        med[j]=np.ma.median(var[j-w/2:j+w/2+1])
        i=n-j-1
        med[i]=np.ma.median(var[i-w/2:i+w/2+1])
    
    return med    
    
####################        

celery = Celery('compute_ndvi', broker='redis://localhost:6379/0')

wd='gs://lillian-bucket-storage/'
#wd='/Users/lilllianpetersen/Google Drive/science_fair/'


vlen=992
hlen=992
start='2015-01-01'
end='2016-12-31'
nyears=2
country='US'
makePlots=False
padding = 16
pixels = vlen+2*padding
res = 120.0

vlen=100
hlen=100
padding=0
pixels=vlen+2*padding
    

clas=["" for x in range(12)]
clasLong=["" for x in range(255)]
clasDict={}
clasNumDict={}
f=open(wd+'data/ground_data.txt')                                
for line in f:
    tmp=line.split(',')
    clasNumLong=int(tmp[0])
    clasLong[clasNumLong]=tmp[1]
    clasNum=int(tmp[3])
    clas[clasNum]=tmp[2]
    
    clasDict[clasLong[clasNumLong]]=clas[clasNum]
    clasNumDict[clasNumLong]=clasNum
    
    
"""function to compute ndvi and make summary plots
variables: lon, lat, pixels, start, end, country, makePlots
"""

#matches=dl.places.find('united-states_washington')
matches=dl.places.find('united-states_iowa')
aoi = matches[0]
shape = dl.places.shape(aoi['slug'], geom='low')

dltiles = dl.raster.dltiles_from_shape(res, vlen, padding, shape)

lonlist=np.zeros(shape=(len(dltiles['features'])))
latlist=np.zeros(shape=(len(dltiles['features'])))
for i in range(len(dltiles['features'])):
    lonlist[i]=dltiles['features'][i]['geometry']['coordinates'][0][0][0]
    latlist[i]=dltiles['features'][i]['geometry']['coordinates'][0][0][1]

features=np.zeros(shape=(len(dltiles['features']),nyears,pixels*pixels,30))
target=np.zeros(shape=(len(dltiles['features']),nyears,pixels*pixels))

@celery.task  
def feature_array(dltile):
    lon=dltile['geometry']['coordinates'][0][0][0]
    lat=dltile['geometry']['coordinates'][0][0][1]
    globals().update(locals())
    print lon
    print lat
    
    
    latsave=str(lat)
    latsave=latsave.replace('.','-')
    lonsave=str(lat)
    lonsave=lonsave.replace('.','-')
    
    print '\n\n'
    print 'dltile: '+str(tile)+' of '+str(len(dltiles['features']))
    
    Mask=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/Mask_2.npy')
    oceanMask=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/oceanMask_2.npy')
    ndviAll=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/ndviAll_2.npy')
    ndwiAll=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/ndwiAll_2.npy')
    month=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/month_2.npy')
    year=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/year_2.npy')
    plotYear=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/plotYear_2.npy')
    n_good_days=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/n_good_days_2.npy')
    arrClas=np.load(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/arrClas_2.npy')
    k=n_good_days
    globals().update(locals())
    ###############################################
    # Claculate Features     
    ############################################### 
    
#    ndviAllMask=np.ones(shape=(ndviAll.shape),dtype=bool)
#    for v in range(pixels):
#        for h in range(pixels):
#    #            if oceanMask[v,h]==1:
#    #                continue
#            for t in range(n_good_days):
#                if ndviAll[v,h,t]!=0 and ndviAll[v,h,t]>-1:
#                    ndviAllMask[v,h,t]=False
    ndviAll=np.ma.masked_array(ndviAll,Mask)
    ndwiAll=np.ma.masked_array(ndwiAll,Mask)
    
    globals().update(locals())
    ########################
    # Average NDVI Monthly #
    ######################## 
    ndviMonths=-9999.*np.ones(shape=(nyears,12,50))
    ndviMonthsMask=np.zeros(shape=(nyears,12,50),dtype=bool)
    ndviMedMonths=-9999.*np.ones(shape=(nyears,pixels,pixels,12))
    ndvi90=np.zeros(shape=(nyears,pixels,pixels,12))
    ndvi10=np.zeros(shape=(nyears,pixels,pixels,12))
    ndwiYears=-9999.*np.ones(shape=(nyears,400))
    ndwiYearsMask=-9999.*np.ones(shape=(nyears,400),dtype=bool)
    ndwi10=np.zeros(shape=(nyears,pixels,pixels))
    ndwi90=np.zeros(shape=(nyears,pixels,pixels))
    
    #    ndwiMonths=-9999.*np.ones(shape=(nyears,12,50))
    #    ndwiMedMonths=-9999.*np.ones(shape=(nyears,pixels,pixels,12))
    #    ndwi90=np.zeros(shape=(nyears,pixels,pixels,12))
    #    ndwi10=np.zeros(shape=(nyears,pixels,pixels,12))
    
    for v in range(pixels):
        for h in range(pixels):  
            if oceanMask[v,h]==True:
                continue
            d=-1*np.ones(shape=(nyears,12),dtype=int)
            i=-1*np.ones(nyears,dtype=int)
            for t in range(n_good_days):
                m=int(month[t])-1
                y=int(year[t]-int(start[0:4]))
                d[y,m]+=1
                i[y]+=1
                ndviMonths[y,m,d[y,m]]=ndviAll[v,h,t]
                ndviMonthsMask[y,m,d[y,m]]=Mask[v,h,t]
                ndwiYears[y,i[y]]=ndwiAll[v,h,t]
                ndwiYearsMask[y,i[y]]=Mask[v,h,t]
    #                    ndwiMonths[y,m,d[y,m]]=ndwiAll[v,h,t]
            
            for y in range(nyears):
               for m in range(12):
                   if d[y,m]>0:
                       if np.ma.is_masked(np.ma.sum(np.ma.masked_array(ndviMonths[y,m,:d[y,m]+1],ndviMonthsMask[y,m,:d[y,m]+1]))) == False:
                          ndviMedMonths[y,v,h,m]=np.ma.median(np.ma.masked_array(ndviMonths[y,m,:d[y,m]+1],ndviMonthsMask[y,m,:d[y,m]+1]))
        #                     ndwiMedMonths[y,v,h,m]=np.median(ndwiMonths[y,m,:d[y,m]+1])
                          ndvi90[y,v,h,m]=np.percentile(  np.ma.masked_array(ndviMonths[y,m,:d[y,m]+1],ndviMonthsMask[y,m,:d[y,m]+1]).compressed()  ,90)
                          ndvi10[y,v,h,m]=np.percentile(  np.ma.masked_array(ndviMonths[y,m,:d[y,m]+1],ndviMonthsMask[y,m,:d[y,m]+1]).compressed()  ,10)
        #                     ndwi90[y,v,h,m]=np.percentile(ndwiMonths[y,m,:d[y,m]+1],90)
        #                     ndwi10[y,v,h,m]=np.percentile(ndwiMonths[y,m,:d[y,m]+1],10)
               ndwi90[y,v,h]=np.percentile(   np.ma.masked_array(ndwiYears[y,:i[y]+1],ndwiYearsMask[y,:i[y]+1]).compressed()  ,90)
               ndwi10[y,v,h]=np.percentile(   np.ma.masked_array(ndwiYears[y,:i[y]+1],ndwiYearsMask[y,:i[y]+1]).compressed()  ,10)
    globals().update(locals())
    ###########################
    
    rollingmed_pix=np.zeros(shape=(pixels,pixels,k))
    rollingmed_pix_ndwi=np.zeros(shape=(pixels,pixels,k))
    for v in range(pixels):
        for h in range(pixels):
            if oceanMask[v,h]==False:
                rollingmed_pix[v,h,:]=rolling_median(ndviAll[v,h,:n_good_days],10)
                rollingmed_pix_ndwi[v,h,:]=rolling_median(ndwiAll[v,h,:k],10)
    
    rollingmed_pix_mask=np.zeros(shape=(rollingmed_pix.shape),dtype=bool)
    for v in range(pixels):
        for h in range(pixels):
            if oceanMask[v,h]==True:
                rollingmed_pix_mask[v,h,:]=True
                continue
            for t in range(len(rollingmed_pix[0,0,:])):
                if math.isnan(rollingmed_pix[v,h,t])==True:
                    rollingmed_pix_mask[v,h,t]=True

    masked_rollingmed_ndvi=np.ma.masked_array(rollingmed_pix,rollingmed_pix_mask)
    masked_rollingmed_ndwi=np.ma.masked_array(rollingmed_pix_ndwi,rollingmed_pix_mask)
    masked_plotYear=np.ma.masked_array(plotYear[0:k],rollingmed_pix_mask[0,0,:])
    
    parA=np.zeros(shape=(nyears,pixels,pixels))
    parB=np.zeros(shape=(nyears,pixels,pixels))
    parC=np.zeros(shape=(nyears,pixels,pixels))
    
    logm1=np.zeros(shape=(nyears,pixels,pixels))
    logb1=np.zeros(shape=(nyears,pixels,pixels))
    logm2=np.zeros(shape=(nyears,pixels,pixels))
    logb2=np.zeros(shape=(nyears,pixels,pixels))
    
    
    stdDev=np.zeros(shape=(nyears,pixels,pixels))
    stdDevNDWI=np.zeros(shape=(nyears,pixels,pixels))
    
    yearlyNDVI=np.zeros(shape=(nyears,pixels,pixels,n_good_days)) # the data divided yearly
    x=np.zeros(shape=(nyears,n_good_days))
    yearlyMask=np.zeros(shape=(nyears,pixels,pixels,n_good_days))
    yearlyNDWI=np.zeros(shape=(nyears,pixels,pixels,n_good_days))
    globals().update(locals())
    i=np.zeros(shape=(nyears),dtype=int)
    # break rollingmed data up into years
    for v in range(pixels):
        for h in range(pixels):
            if oceanMask[v,h]==True:
                continue
            i[:]=-1
            itmp=0
            for t in range(len(masked_rollingmed_ndvi[0,0,:])):
                if np.ma.is_masked(masked_rollingmed_ndvi[v,h,t])==False:
                    y=int(year[t]-int(start[0:4]))
                    i[y]+=1
                    yearlyNDVI[y,v,h,i[y]]=masked_rollingmed_ndvi[v,h,t]
                    yearlyNDWI[y,v,h,i[y]]=masked_rollingmed_ndwi[v,h,t]
                    x[y,i[y]]=masked_plotYear[t]
                    yearlyMask[y,v,h,i[y]]=rollingmed_pix_mask[v,h,t]
    globals().update(locals())
    yearlyNDVI=np.ma.masked_array(yearlyNDVI,yearlyMask)
    yearlyNDWI=np.ma.masked_array(yearlyNDWI,yearlyMask)
    for y in range(nyears):
        x[y]=np.ma.masked_array(x[y],yearlyMask[y,0,0,:])

    for y in range(nyears):
        itmp=int(i[y])
        for v in range(pixels):
            for h in range(pixels):
                stdDev[y,v,h]=np.ma.std(yearlyNDVI[y,v,h,:itmp])
                stdDevNDWI[y,v,h]=np.ma.std(yearlyNDWI[y,v,h,:itmp])
        
                parA[y,v,h],parB[y,v,h],parC[y,v,h]=np.polyfit(x[y,:itmp],yearlyNDVI[y,v,h,:itmp],2)

#                logm1[y,v,h],logb1[y,v,h]=np.polyfit(x[y,:itmp/2], np.ma.log(yearlyNDVI[y,v,h,:itmp/2]), 1)
#                logm2[y,v,h],logb2[y,v,h]=np.polyfit(x[y,itmp/2:itmp], np.ma.log(yearlyNDVI[y,v,h,itmp/2:itmp]), 1)
#                
#                if makePlots:
#                    yfit=parA[y,v,h]*x[y,:itmp]**2+parB[y,v,h]*x[y,:itmp]+parC[y,v,h]
#                    plt.clf()
#                    plt.plot(x[y,:itmp],yfit,'.')
#                    plt.plot(x[y,:itmp],yearlyNDVI[y,v,h,:itmp],'.')
#                    plt.ylim(0,1)
        #            plt.savefig(wd+'figures/parabola_'+lonsave+'_'+latsave+'_2015.pdf')
    
    
    stdDevR=np.reshape(stdDev,[nyears,pixels*pixels],order='C')
    stdDevNDWIR=np.reshape(stdDevNDWI,[nyears,pixels*pixels],order='C')
    parAr=np.reshape(parA,[nyears,pixels*pixels],order='C')
    parBr=np.reshape(parB,[nyears,pixels*pixels],order='C')
    parCr=np.reshape(parC,[nyears,pixels*pixels],order='C')
    
    ndvi90R=np.reshape(ndvi90,[nyears,pixels*pixels,12],order='C')
    ndvi10R=np.reshape(ndvi10,[nyears,pixels*pixels,12],order='C')
    
    ndwi90R=np.reshape(ndwi90,[nyears,pixels*pixels],order='C')
    ndwi10R=np.reshape(ndwi10,[nyears,pixels*pixels],order='C')
     
    arrClasR=np.reshape(arrClas,[pixels*pixels],order='C')

    for y in range(nyears):
        for p in range(pixels*pixels):
    #            print s
            features[tile,y,p,0]=ndvi90R[y,p,0]
            features[tile,y,p,1]=ndvi90R[y,p,1]
            features[tile,y,p,2]=ndvi90R[y,p,2]
            features[tile,y,p,3]=ndvi90R[y,p,3]
            features[tile,y,p,4]=ndvi90R[y,p,4]
            features[tile,y,p,5]=ndvi90R[y,p,5]
            features[tile,y,p,6]=ndvi90R[y,p,6]
            features[tile,y,p,7]=ndvi90R[y,p,7]
            features[tile,y,p,8]=ndvi90R[y,p,8]
            features[tile,y,p,9]=ndvi90R[y,p,9]
            features[tile,y,p,10]=ndvi90R[y,p,10]
            features[tile,y,p,11]=ndvi90R[y,p,11]
            
            features[tile,y,p,12]=ndvi10R[y,p,0]
            features[tile,y,p,13]=ndvi10R[y,p,1]
            features[tile,y,p,14]=ndvi10R[y,p,2]
            features[tile,y,p,15]=ndvi10R[y,p,3]
            features[tile,y,p,16]=ndvi10R[y,p,4]
            features[tile,y,p,17]=ndvi10R[y,p,5]
            features[tile,y,p,18]=ndvi10R[y,p,6]
            features[tile,y,p,19]=ndvi10R[y,p,7]
            features[tile,y,p,20]=ndvi10R[y,p,8]
            features[tile,y,p,21]=ndvi10R[y,p,9]
            features[tile,y,p,22]=ndvi10R[y,p,10]
            features[tile,y,p,23]=ndvi10R[y,p,11]
            
            features[tile,y,p,24]=ndwi90R[y,p]
            features[tile,y,p,25]=ndwi10R[y,p]
            features[tile,y,p,26]=stdDevNDWIR[y,p]
            
            features[tile,y,p,27]=stdDevR[y,p]
            features[tile,y,p,28]=parAr[y,p]
            features[tile,y,p,29]=parBr[y,p]
            features[tile,y,p,30]=parCr[y,p]
        
            target[tile,y,p]=arrClasR[p]
            
                
    
                
    ########################
    # Save variables       #
    ######################## 
    np.save(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/target',target)
    np.save(wd+'saved_vars/'+str(lon)+'_'+str(lat)+'/features',features)
    ########################


#for tile in range(len(dltiles['features'])):
#
for tile in range(1):
    tile=4
    dltile=dltiles['features'][tile]
    feature_array(dltile)

#for i in range(len(dltiles['features'])):
#    if not os.path.exists(r'../saved_vars/'+str(lonlist[i])+'_'+str(latlist[i])+'/features'):
#        tile=i
#        dltile=dltiles['features'][i]
#        feature_array(dltile)
#    




'''
targetR=np.reshape(target[:tile],tile*nyears*pixels*pixels)

sklearn.preprosessing.StandardScaler

for n in range(len(targetR)):
    if targetR[n]==1 or targetR[n]==2:
        targetR[n]=1
    elif targetR[n]==3 or targetR[n]==4:
        targetR[n]=2
    else:
        targetR[n]=targetR[n]-2
        
X=StandardScaler().fit_transform(featuresR)        


clf = svm.LinearSVC()
clf.fit()  
clf.predict()


#ytst=10**(mtst*xtst+btst)+np.random.rand(180)*10
#
#m,b=np.polyfit(xtst, np.log10(ytst), 1)
#
#yfit=10**(m*xtst+b)
#
#plt.plot(xtst,ytst)
#plt.plot(xtst,yfit)
'''
