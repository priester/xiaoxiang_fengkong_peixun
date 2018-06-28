# -*- coding: utf-8 -*
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from time import strptime,mktime
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn import cross_validation, metrics
from common.const import *
from featureEngineering.featureEncoding.categorical_feature_encoding import CategoricalFeatureEncoding
from featureEngineering.featureEncoding.numeric_feature_encoding import NumericFeatureEncoding
from modeling.modelTrain.regression_model import RegressionModel
from modeling.parameterAdjust.parameter_adjust import ParameterAdjust

if __name__ == '__main__':
    print('--还款率预测模型开始执行--')
    '''
    第一步：文件准备
    '''
    #读取源数据，FOLD_OF_DATA保存原始数据路径，SRC_FILE_NAME保存数据文件名称
    mydata = pd.read_csv(const.FOLD_OF_DATA + const.SRC_FILE_NAME, header=0)
    #催收还款率等于催收金额/（所欠本息+催收费用）。其中催收费用以支出形式表示
    #催收还款率作为样本的label
    mydata['rec_rate'] = mydata.apply(
        lambda x: x.LP_NonPrincipalRecoverypayments / (x.AmountDelinquent + x.LP_CollectionFees), axis=1)
    #对样本label进行处理，当label值大于1时，设置label值为1
    mydata['rec_rate'] = mydata['rec_rate'].map(lambda x: min(x, 1))

    #整个开发数据分为训练集、测试集2个部分
    #其中训练集占60%，测试集占40%
    trainData, testData = train_test_split(mydata, test_size=0.4)

    '''
    第二步：数据预处理
    '''
    #类别型特征
    categoricalFeatures = const.CATEGORICAL_FEATURES
    print(categoricalFeatures)
    #数值型特征
    numFeatures = const.NUM_FEATURES
    print(numFeatures)

    '''
    类别型变量需要用目标变量的均值进行编码
    '''
    trainData, encodedFeatures = CategoricalFeatureEncoding.feature_encoding_process(categoricalFeatures, trainData)

    '''
    对数值型数据的缺失进行补缺
    '''
    trainData = NumericFeatureEncoding.feature_encoding_process(numFeatures, trainData)

    #将从原始类别型特征扩展出来的编码型特征，与数值型特征，合并在一起，作为最终用于模型训练的特征，保存在numFeatures2中
    numFeatures2 = numFeatures + encodedFeatures

    '''
    第三步：调参
    对基于CART的随机森林的调参，主要有：
    1，树的个数
    2，树的最大深度
    3，内部节点最少样本数与叶节点最少样本数
    4，特征个数

    此外，调参过程中选择的误差函数是均值误差，5倍折叠
    '''
    #X保存样本特征，y保存样本label
    X, y = trainData[numFeatures2], trainData['rec_rate']
    #调参
    best_n_estimators, best_max_depth, best_min_samples_leaf, best_min_samples_split, best_max_features = ParameterAdjust.gridSearchCVParameterAdjust(X, y, numFeatures2)
    #模型训练
    cls = RegressionModel.RandomForestRegressorTrain(best_n_estimators,
                                                     best_max_depth,
                                                     best_min_samples_leaf,
                                                     best_min_samples_split,
                                                     best_max_features,
                                                     X,
                                                     y)
    #模型精确度验证
    RegressionModel.RandomForestRegressorTrainTest(cls, trainData, numFeatures2)

    '''
    第四步：在测试集上测试效果
    '''
    #处理类别型特征
    testData, encodedFeatures = CategoricalFeatureEncoding.feature_encoding_process(categoricalFeatures, testData)

    #处理数值型特征
    testData = NumericFeatureEncoding.feature_encoding_process(numFeatures, testData)

    #使用模型对测试集样本进行预测
    RegressionModel.RandomForestRegressorTrainTest(cls, testData, numFeatures2)
    print('--还款率预测模型结束执行--')

