import random
import json
import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from kneed import KneeLocator

Anatreada_graphical=False
if (Anatreada_graphical):
    import matplotlib.pyplot as plt

# file : str
try:
    file = "../nodes.json"
except FileNotFoundError as e:
    print("File not found : the path to you 'nodes.json' may be uncorrect!")
    logging.warning("An error occurred : " + e)
    

# The json file should have this example of format :
# {
#     "nodes": [
#         {
#             "title": "xxxxxxxxxx",
#             "url": "https://xxxxxxxxx/xxxxxxxxxxx.xxx",
#             "usersNotes": "xxxxxxx",
#             "comment": "xxxxxxxx",
#             "name": "xxxxxxxxxx",
#             "tags": [
#                 "{tagName,minValue,value,maxValue}",
#                 "{tagName1,minValue,value,maxValue}",
#                 "{tagName2,minValue,value,maxValue}",
#                 "tagName3"
#              ]
#         }
# }

def test(c):
    return "test" + c

def elbow_method_for_optimal_K(data_frame):
    """DataFrame() -> void
    Initialise k-means and use the inertia attribute 
    to identify the sum of squared distances of samples 
    to the nearest cluster centre.
    Returns the optimal knee value"""

    # sum_of_squared_distances : list()
    sum_of_squared_distances = []
    K = range(1,20)
    
    for k in K:
        km = KMeans(n_clusters=k)
        km = km.fit(data_frame)
        sum_of_squared_distances.append(km.inertia_)
    
    x = range(1, len(sum_of_squared_distances)+1)

    kn = KneeLocator(x, sum_of_squared_distances, curve='convex', direction='decreasing')
    print(kn.knee)

    """
    plt.title('Elbow Method For Optimal k')
    plt.xlabel('Number of clusters k')
    plt.ylabel('Sum of squared distances')
    plt.plot(x, sum_of_squared_distances, 'bx-')
    plt.vlines(kn.knee, plt.ylim()[0], plt.ylim()[1], linestyles='dashed')
    plt.show()
    """

    return kn.knee

def pca_on_one_node(nodes_json_text):

    # node_dict : dict()
    # node_dict contains all the json text
    json_dict = json.loads(nodes_json_text)

    # nodes_list : list(dict())
    # nodes_list contains all nodes/tiles information in a list of dictonaries format
    nodes_list = json_dict["nodes"]
    nodes_list_clean = nodes_list
    # remove former "group" tag in tags list
    # map(remove_group_from_list, nodes_list)

    #for i in range(0, len(nodes_list)):
    #    for j in range(0, len(nodes_list[i]["tags"])) :
    #        if ("_group_" in nodes_list[i]["tags"][j]) and ("{" not in nodes_list[i]["tags"][j]) and ("}" not in nodes_list[i]["tags"][j]) :
    #            nodes_list_clean[i]["tags"].pop(j)
    
    
    for i in range(0, len(nodes_list)):        
        for j, tag in enumerate(nodes_list_clean[i]["tags"]):
            if ("_group_" in tag) and ("{" not in tag) and ("}" not in tag):
                nodes_list_clean[i]["tags"].pop(j)
                continue


    # df_nodes_normalized : DataFrame()
    # df_nodes_normalized contains the DataFrame of nodes_list_clean
    df_nodes_normalized = pd.json_normalize(nodes_list_clean)

    # df_column_tag_normalized : DataFrame()
    # df_column_tag_normalized contains the DataFrame of tags column of df_nodes_normalized DataFrame
    df_column_tag_normalized = df_nodes_normalized["tags"]
    print(df_column_tag_normalized)
    # tags_normalized : DataFrame()
    # tags_normalized contains the DataFrame of node/tile tags
    df_tags_normalized = pd.DataFrame()

    # tag_lines : list(dict())
    # tag_lines contains tags information in a dictionary format
    tag_lines = []

    #i : int
    for i in range(0, len(df_column_tag_normalized)):
        # dict_line : dict()
        dict_line = dict()
        # j : int
        for j in range(0, len(df_column_tag_normalized[i])):

            newline = df_column_tag_normalized[i][j]
            newline = newline.replace("{", "")
            newline = newline.replace("}", "")

            # list_line : []
            # list_line contains the list of elements of le string line
            list_line = newline.split(',')

            # tag_name : str
            tag_name = list_line[0]

            # if it's a variable tag
            if len(list_line) > 1:
                value_min =     list_line[1]
                value =         list_line[2]
                value_man =     list_line[3]
                dict_line[tag_name] = float(value)

            # if the tag is the last of the node/tile
            if j == len(df_column_tag_normalized[i]) -1 :
                tag_lines.append(dict_line)
                dict_line = {}

    
    df_tags_normalized = pd.json_normalize(tag_lines)
    #print("--------------------------------------- TAG DATAFRAME NORMALIZED -----------------------------------------------------------")
    #print(df_tags_normalized)
    #print("----------------------------------------------------------------------------------------------------------------------------")

    # Drop rows with missing value -> uncomment the next line if you want it
    # df_tags_normalized = df_tags_normalized.dropna()

    # feature : list(str)
    # features contains yhe list of column/feature names
    features = []
    features = df_tags_normalized.columns.values

    # replacing NaN values by the median using -> .median()
    # replacing NaN values by the mean average using -> .mean()
    # replacing NaN values by the standard deviation using -> .std()

    for feature in features:
        df_tags_normalized[feature] = df_tags_normalized[feature].replace(np.NAN, df_tags_normalized[feature].mean())
    
    nb_lines, nb_columns = df_tags_normalized.shape
    print(df_tags_normalized)
    # print("-------------------------------- TAG DATAFRAME NORMALIZED WITH MEAN INSTEAD OF NAN ------------------------------------------")
    # print(df_tags_normalized)
    # print("-----------------------------------------------------------------------------------------------------------------------------")

    # --------------------------------------------- K-MEANS CLUSTERING ---------------------------------------------
    
    # Declaring Model
    knee = elbow_method_for_optimal_K(df_tags_normalized)
    model = KMeans(n_clusters = knee)
    model.fit(df_tags_normalized)

    # Make a prediction
    prediction = np.arange(len(features))
    predicted_label = model.predict([prediction])
    
    # Clustering ...
    labels = model.labels_
    clusters = model.cluster_centers_
    
    # Add "group" column to features
    features_labels = np.append(features, 'group')

    # Reshape the array of labels to have a column shape
    labels = np.reshape(labels, (nb_lines, 1))

    # Concatenate arraya of data "df_tags_normalized" and labels "labels"
    final_df_tags_normalized = np.concatenate([df_tags_normalized, labels], axis=1)

    # Create tags dataset
    tags_dataset = pd.DataFrame(final_df_tags_normalized)
    tags_dataset.columns = features_labels

    """
    # Replace cluster number by a formated group name like "00_group"
    targets = np.empty(0) # Will be used to attribut them a color in the graph

    for i in range(0, len(clusters)):
        name_group = ""
        if i > 9:
            name_group = str(i) + "_group"
        else:
            name_group = "0" + str(i) + "_group"
        tags_dataset["group"].replace(i, name_group, inplace = True)
        targets = np.append(targets, name_group)
    """

    # Replace cluster number by a formated group name like "00_group_1"
    targets = np.empty(0) # Will be used to attribut them a color in the graph

    for i in range(0, len(clusters)):
        name_group = ""
        name_group = "00" + "_group_" + str(i + 1)
        tags_dataset["group"].replace(i, name_group, inplace = True)
        targets = np.append(targets, name_group)

    print(tags_dataset)
    # --------------------------------------------- PCA ---------------------------------------------
    
    # Assign values of tags dataset exept groups to x
    x = tags_dataset.loc[:, features].values

    # Normalizing the features : each feature of your data should be 
    # normally distributed such that it will scale the distribution 
    # to a mean of zero and a standard deviation of one
    x = StandardScaler().fit_transform(x)
    feat_cols = ["feature" + str(i) for i in range(0, x.shape[1])]
    normalized_tags = pd.DataFrame(x, columns = feat_cols)

    # print("Normalized tags : \n", normalized_tags.tail())

    # Projecting the thirty-dimensional Tags Data to two-dimensional
    pca_tags = PCA(n_components = 2)
    principal_component_tags = pca_tags.fit_transform(x)
    df_principal_tags = pd.DataFrame(data = principal_component_tags,
                columns = ["Principal Component 1", "Principal Component 2"])
    
    # print('Explained variation per principal component: {}'.format(pca_tags.explained_variance_ratio_))

    if (Anatreada_graphical):
        # Visualization of the n samples along the Principal Component - 1
        # and Principal Component - 2 axis
        plt.figure(figsize=(10,10))
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=14)
        plt.xlabel("Principal Component - 1",fontsize=20)
        plt.ylabel("Principal Component - 2",fontsize=20)
        plt.title("Principal Component Analysis of Tag Wikimedia Dataset (NaN -> mean average)",fontsize=20)
    
        # Colors of clusters
        colors = []
        for target in targets:
            r = random.random()
            b = random.random()
            g = random.random()
            color = (r, g, b)
            colors.append(color)
    
        for target, color in zip(targets,colors):
            indicesToKeep = tags_dataset["group"] == target
            plt.scatter(df_principal_tags.loc[indicesToKeep, "Principal Component 1"]
                        , df_principal_tags.loc[indicesToKeep, "Principal Component 2"], c = color, s = 50)

        plt.legend(targets,prop={"size": 15})
    
        #plt.show()

    # ------------------------------- Reformating Dataframe into json --------------------------------
    #   |_ get the column "group"
    #   |_ associate each row to each nodes with the following format : "{name_of_group}"
    """
    for i in range(0, len(nodes_list_clean)):
        nodes_list_clean[i]["tags"].append("{" + tags_dataset["group"][i] + "}")
    """
    #   |_ associate each row to each nodes with the following format : "name_of_group"
    for i in range(0, len(nodes_list)):
        nodes_list_clean[i]["tags"].append(tags_dataset["group"][i])

    nodes_dict_node = dict()
    nodes_dict_node["nodes"] = nodes_list_clean

    json_tiles_text = json.dumps(nodes_dict_node)

    return json_tiles_text


def pca_on_multiple_nodes(nodes_json_text):

    # node_dict : dict()
    # node_dict contains all the json text
    json_dict = json.loads(nodes_json_text)

    # nodes_list : list(dict())
    # nodes_list contains all nodes/tiles information in a list of dictonaries format
    nodes_list = json_dict["nodes"]
    nodes_list_clean = nodes_list
    # remove former "group" tag in tags list
    # map(remove_group_from_list, nodes_list)

    #for i in range(0, len(nodes_list)):
    #    for j in range(0, len(nodes_list[i]["tags"])) :
    #        if ("_group_" in nodes_list[i]["tags"][j]) and ("{" not in nodes_list[i]["tags"][j]) and ("}" not in nodes_list[i]["tags"][j]) :
    #            nodes_list_clean[i]["tags"].pop(j)
    
    
    for i in range(0, len(nodes_list)):        
        for j, tag in enumerate(nodes_list_clean[i]["tags"]):
            if ("_group_" in tag) and ("{" not in tag) and ("}" not in tag):
                nodes_list_clean[i]["tags"].pop(j)
                continue


    # df_nodes_normalized : DataFrame()
    # df_nodes_normalized contains the DataFrame of nodes_list_clean
    df_nodes_normalized = pd.json_normalize(nodes_list_clean)

    # df_column_tag_normalized : DataFrame()
    # df_column_tag_normalized contains the DataFrame of tags column of df_nodes_normalized DataFrame
    df_column_tag_normalized = df_nodes_normalized["tags"]
    print(df_column_tag_normalized)
    # tags_normalized : DataFrame()
    # tags_normalized contains the DataFrame of node/tile tags
    df_tags_normalized = pd.DataFrame()

    # tag_lines : list(dict())
    # tag_lines contains tags information in a dictionary format
    tag_lines = []

    #i : int
    for i in range(0, len(df_column_tag_normalized)):
        # dict_line : dict()
        dict_line = dict()
        # j : int
        for j in range(0, len(df_column_tag_normalized[i])):

            newline = df_column_tag_normalized[i][j]
            newline = newline.replace("{", "")
            newline = newline.replace("}", "")

            # list_line : []
            # list_line contains the list of elements of le string line
            list_line = newline.split(',')

            # tag_name : str
            tag_name = list_line[0]

            # if it's a variable tag
            if len(list_line) > 1:
                value_min =     list_line[1]
                value =         list_line[2]
                value_man =     list_line[3]
                dict_line[tag_name] = float(value)

            # if the tag is the last of the node/tile
            if j == len(df_column_tag_normalized[i]) -1 :
                tag_lines.append(dict_line)
                dict_line = {}

    
    df_tags_normalized = pd.json_normalize(tag_lines)
    #print("--------------------------------------- TAG DATAFRAME NORMALIZED -----------------------------------------------------------")
    #print(df_tags_normalized)
    #print("----------------------------------------------------------------------------------------------------------------------------")

    # Drop rows with missing value -> uncomment the next line if you want it
    # df_tags_normalized = df_tags_normalized.dropna()

    # feature : list(str)
    # features contains yhe list of column/feature names
    features = []
    features = df_tags_normalized.columns.values

    # replacing NaN values by the median using -> .median()
    # replacing NaN values by the mean average using -> .mean()
    # replacing NaN values by the standard deviation using -> .std()

    for feature in features:
        df_tags_normalized[feature] = df_tags_normalized[feature].replace(np.NAN, df_tags_normalized[feature].mean())
    
    nb_lines, nb_columns = df_tags_normalized.shape
    print(df_tags_normalized)
    # print("-------------------------------- TAG DATAFRAME NORMALIZED WITH MEAN INSTEAD OF NAN ------------------------------------------")
    # print(df_tags_normalized)
    # print("-----------------------------------------------------------------------------------------------------------------------------")

    # --------------------------------------------- K-MEANS CLUSTERING ---------------------------------------------
    
    # Declaring Model
    knee = elbow_method_for_optimal_K(df_tags_normalized)
    model = KMeans(n_clusters = knee)
    model.fit(df_tags_normalized)

    # Make a prediction
    prediction = np.arange(len(features))
    predicted_label = model.predict([prediction])
    
    # Clustering ...
    labels = model.labels_
    clusters = model.cluster_centers_
    
    # Add "group" column to features
    features_labels = np.append(features, 'group')

    # Reshape the array of labels to have a column shape
    labels = np.reshape(labels, (nb_lines, 1))

    # Concatenate arraya of data "df_tags_normalized" and labels "labels"
    final_df_tags_normalized = np.concatenate([df_tags_normalized, labels], axis=1)

    # Create tags dataset
    tags_dataset = pd.DataFrame(final_df_tags_normalized)
    tags_dataset.columns = features_labels

    """
    # Replace cluster number by a formated group name like "00_group"
    targets = np.empty(0) # Will be used to attribut them a color in the graph

    for i in range(0, len(clusters)):
        name_group = ""
        if i > 9:
            name_group = str(i) + "_group"
        else:
            name_group = "0" + str(i) + "_group"
        tags_dataset["group"].replace(i, name_group, inplace = True)
        targets = np.append(targets, name_group)
    """

    # Replace cluster number by a formated group name like "00_group_1"
    targets = np.empty(0) # Will be used to attribut them a color in the graph

    for i in range(0, len(clusters)):
        name_group = ""
        name_group = "00" + "_group_" + str(i + 1)
        tags_dataset["group"].replace(i, name_group, inplace = True)
        targets = np.append(targets, name_group)

    print(tags_dataset)
    # --------------------------------------------- PCA ---------------------------------------------
    
    # Assign values of tags dataset exept groups to x
    x = tags_dataset.loc[:, features].values

    # Normalizing the features : each feature of your data should be 
    # normally distributed such that it will scale the distribution 
    # to a mean of zero and a standard deviation of one
    x = StandardScaler().fit_transform(x)
    feat_cols = ["feature" + str(i) for i in range(0, x.shape[1])]
    normalized_tags = pd.DataFrame(x, columns = feat_cols)

    # print("Normalized tags : \n", normalized_tags.tail())

    # Projecting the thirty-dimensional Tags Data to two-dimensional
    pca_tags = PCA(n_components = 2)
    principal_component_tags = pca_tags.fit_transform(x)
    df_principal_tags = pd.DataFrame(data = principal_component_tags,
                columns = ["Principal Component 1", "Principal Component 2"])
    
    # print('Explained variation per principal component: {}'.format(pca_tags.explained_variance_ratio_))

    # Visualization of the n samples along the Principal Component - 1
    # and Principal Component - 2 axis
    if (Anatreada_graphical):
        plt.figure(figsize=(10,10))
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=14)
        plt.xlabel("Principal Component - 1",fontsize=20)
        plt.ylabel("Principal Component - 2",fontsize=20)
        plt.title("Principal Component Analysis of Tag Wikimedia Dataset (NaN -> mean average)",fontsize=20)
    
        # Colors of clusters
        colors = []
        for target in targets:
            r = random.random()
            b = random.random()
            g = random.random()
            color = (r, g, b)
            colors.append(color)
    
        for target, color in zip(targets,colors):
            indicesToKeep = tags_dataset["group"] == target
            plt.scatter(df_principal_tags.loc[indicesToKeep, "Principal Component 1"]
                        , df_principal_tags.loc[indicesToKeep, "Principal Component 2"], c = color, s = 50)

        plt.legend(targets,prop={"size": 15})
            
        #plt.show()

    # ------------------------------- Reformating Dataframe into json --------------------------------
    #   |_ get the column "group"
    #   |_ associate each row to each nodes with the following format : "{name_of_group}"
    """
    for i in range(0, len(nodes_list_clean)):
        nodes_list_clean[i]["tags"].append("{" + tags_dataset["group"][i] + "}")
    """
    #   |_ associate each row to each nodes with the following format : "name_of_group"
    groups_dict = dict()
    for i in range(0, len(nodes_list)):
        nodes_list_clean[i]["tags"].append(tags_dataset["group"][i])
        groups_dict[nodes_list_clean[i]["id"]] = tags_dataset["group"][i]

    nodes_dict_node = dict()
    nodes_dict_node["nodes"] = nodes_list_clean

    json_tiles_text = json.dumps(nodes_dict_node)

    groups_dict = json.dumps(groups_dict)

    return (json_tiles_text, groups_dict)


def pca_test():

    with open(file) as nodes_json_file:

        # node_dict : dict()
        # node_dict contains all the json file
        json_dict = json.load(nodes_json_file)

        # nodes_list : list(dict())
        # nodes_list contains all nodes/tiles information in a list of dictonaries format
        nodes_list = json_dict["nodes"]
        
        # df_nodes_normalized : DataFrame()
        # df_nodes_normalized contains the DataFrame of nodes_list
        df_nodes_normalized = pd.json_normalize(nodes_list)

        # df_column_tag_normalized : DataFrame()
        # df_column_tag_normalized contains the DataFrame of tags column of df_nodes_normalized DataFrame
        df_column_tag_normalized = df_nodes_normalized["tags"]
        print(df_column_tag_normalized)
        # tags_normalized : DataFrame()
        # tags_normalized contains the DataFrame of node/tile tags
        df_tags_normalized = pd.DataFrame()

        # tag_lines : list(dict())
        # tag_lines contains tags information in a dictionary format
        tag_lines = []

        #i : int
        for i in range(0, len(df_column_tag_normalized)):
            # dict_line : dict()
            dict_line = dict()
            # j : int
            for j in range(0, len(df_column_tag_normalized[i])):

                newline = df_column_tag_normalized[i][j]
                newline = newline.replace("{", "")
                newline = newline.replace("}", "")

                # list_line : []
                # list_line contains the list of elements of le string line
                list_line = newline.split(',')

                # tag_name : str
                tag_name = list_line[0]

                # if it's a variable tag
                if len(list_line) > 1:
                    value_min =     list_line[1]
                    value =         list_line[2]
                    value_man =     list_line[3]
                    dict_line[tag_name] = float(value)

                # if the tag is the last of the node/tile
                if j == len(df_column_tag_normalized[i]) -1 :
                    tag_lines.append(dict_line)
                    dict_line = {}

        
        df_tags_normalized = pd.json_normalize(tag_lines)
        #print("--------------------------------------- TAG DATAFRAME NORMALIZED -----------------------------------------------------------")
        #print(df_tags_normalized)
        #print("----------------------------------------------------------------------------------------------------------------------------")

        # Drop rows with missing value -> uncomment the next line if you want it
        # df_tags_normalized = df_tags_normalized.dropna()

        # feature : list(str)
        # features contains yhe list of column/feature names
        features = []
        features = df_tags_normalized.columns.values

        # replacing NaN values by the median using -> .median()
        # replacing NaN values by the mean average using -> .mean()
        # replacing NaN values by the standard deviation using -> .std()

        for feature in features:
            df_tags_normalized[feature] = df_tags_normalized[feature].replace(np.NAN, df_tags_normalized[feature].mean())
        
        nb_lines, nb_columns = df_tags_normalized.shape
        print(df_tags_normalized)
        # print("-------------------------------- TAG DATAFRAME NORMALIZED WITH MEAN INSTEAD OF NAN ------------------------------------------")
        # print(df_tags_normalized)
        # print("-----------------------------------------------------------------------------------------------------------------------------")

        # --------------------------------------------- K-MEANS CLUSTERING ---------------------------------------------
        
        # Declaring Model
        knee = elbow_method_for_optimal_K(df_tags_normalized)
        model = KMeans(n_clusters = knee)
        model.fit(df_tags_normalized)

        # Make a prediction
        prediction = np.arange(len(features))
        predicted_label = model.predict([prediction])
        
        # Clustering ...
        labels = model.labels_
        clusters = model.cluster_centers_
        
        # Add "group" column to features
        features_labels = np.append(features, 'group')

        # Reshape the array of labels to have a column shape
        labels = np.reshape(labels, (nb_lines, 1))

        # Concatenate arraya of data "df_tags_normalized" and labels "labels"
        final_df_tags_normalized = np.concatenate([df_tags_normalized, labels], axis=1)

        # Create tags dataset
        tags_dataset = pd.DataFrame(final_df_tags_normalized)
        tags_dataset.columns = features_labels

        # Replace cluster number by a formated group name like "0_group"
        targets = np.empty(0) # Will be used to attribut them a color in the graph
        for i in range(0, len(clusters)):
            name_group = ""
            if i > 9:
                name_group = str(i) + "_group"
            else:
                name_group = "0" + str(i) + "_group"
            tags_dataset["group"].replace(i, name_group, inplace = True)
            targets = np.append(targets, name_group)

        print(tags_dataset)
        # --------------------------------------------- PCA ---------------------------------------------
        
        # Assign values of tags dataset exept groups to x
        x = tags_dataset.loc[:, features].values

        # Normalizing the features : each feature of your data should be 
        # normally distributed such that it will scale the distribution 
        # to a mean of zero and a standard deviation of one
        x = StandardScaler().fit_transform(x)
        feat_cols = ["feature" + str(i) for i in range(0, x.shape[1])]
        normalized_tags = pd.DataFrame(x, columns = feat_cols)

        # print("Normalized tags : \n", normalized_tags.tail())

        # Projecting the thirty-dimensional Tags Data to two-dimensional
        pca_tags = PCA(n_components = 2)
        principal_component_tags = pca_tags.fit_transform(x)
        df_principal_tags = pd.DataFrame(data = principal_component_tags,
                    columns = ["Principal Component 1", "Principal Component 2"])
        
        # print('Explained variation per principal component: {}'.format(pca_tags.explained_variance_ratio_))

        # Visualization of the n samples along the Principal Component - 1
        # and Principal Component - 2 axis
        if (Anatreada_graphical):
            plt.figure(figsize=(10,10))
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=14)
            plt.xlabel("Principal Component - 1",fontsize=20)
            plt.ylabel("Principal Component - 2",fontsize=20)
            plt.title("Principal Component Analysis of Tag Wikimedia Dataset (NaN -> mean average)",fontsize=20)
        
            # Colors of clusters
            colors = []
            for target in targets:
                r = random.random()
                b = random.random()
                g = random.random()
                color = (r, g, b)
                colors.append(color)
        
            for target, color in zip(targets,colors):
                indicesToKeep = tags_dataset["group"] == target
                plt.scatter(df_principal_tags.loc[indicesToKeep, "Principal Component 1"]
                            , df_principal_tags.loc[indicesToKeep, "Principal Component 2"], c = color, s = 50)

            plt.legend(targets,prop={"size": 15})
        
            # plt.show()

        # => Observation :   
        #       1 - When missing data of samples are replacing by the mean or the median, the lack of 
        #           relevant data set distorts the analysis. Clusters are not distinctive
        #       2 - When samples containing missing data are removed from the data set, clusters are 
        #           visible because of the accuracy of the data set.


        # ------------------------------- Reformating Dataframe into json --------------------------------
        #   |_ get the column "group"
        #   |_ associate each row to each nodes with the following format : "{name_of_group}"
        
        for i in range(0, len(nodes_list)):
            nodes_list[i]["tags"].append("{" + tags_dataset["group"][i] + "}")

        json_tiles_text = json.dumps(nodes_list)

        return json_tiles_text

