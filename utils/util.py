import os
import torch
import torchvision
import matplotlib.pyplot as plt
import numpy as np
import json
import math
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels
from PIL import Image
from ipywidgets import widgets, interact
from pprint import pprint

'''
utils that do not serve a broader purpose, and generally are used for visualization or otherwise
'''

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def visualizeDataset(dataloader):
    '''
    Visualize a batch of tensors
    '''
    images, labels = next(iter(dataloader))
    plt.imshow(torchvision.utils.make_grid(images, nrow=8).permute(1, 2, 0))
    
    
def visualizeBatch(dataloader, normalized):
    '''
    Visualize all the images in a batch in a subplot
    Visualize one image as its own figure
    '''
    images, labels = next(iter(dataloader))
    #print(images.shape) # [batch size, channels, depth, height, width] 
    
    img = images[0]
    if len(img.shape) > 3: 
        #img = img.permute(0,2,1,3)
        img = np.squeeze(img.numpy())
        
        lab = np.squeeze(labels[0])
        classes = ['glom', 'pct', 'tal', 'CD45', 'dct']
        def update_layer(layer = 0):
            plt.imshow(img[layer], cmap ='gray')
            plt.show()
            
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        plt.title("Class is : " + classes[lab])
        plt.imshow(img[0], cmap ='gray')
        interact(update_layer, layer=widgets.IntSlider(min=0,max=img.shape[0]-1,step=1,value=0))
        
        '''
        for i in range(img.shape[1]):
            img32 = img[0][i]
            #print(img32.shape)
            #img32 = (img32 + abs(np.amin(img32))) / (abs(np.amin(img32))+abs(np.amax(img32)))
            img32 = Image.fromarray(img32)
            plt.imshow(img32)
            plt.show() 
            '''
        return
    
    img = unnormTensor(images[0], normalized)
    plt.imshow(img, cmap='gray')
    plt.show()
    plt.hist(np.ravel(img), 255, range=[0.01,1])
    plt.show()
    fig = plt.figure(figsize=(40, 40))
    batch = math.ceil(math.sqrt(dataloader.batch_size))
    for i in range(len(images)):
        a = fig.add_subplot(batch,batch,i+1)
        img = unnormTensor(images[i], normalized)
        imgplot = plt.imshow(img) #have to unnormalize data first!
        plt.axis('off')
        a.set_title("Label = " +str(labels[i].numpy()), fontsize=30)

def unnormTensor(tens, normalized):
    '''
    Takes a image tensor and returns the un-normalized numpy array scaled to [0,1]
    '''
    mean = [0.485, 0.456, 0.406]
    std =[0.229, 0.224, 0.225]
    img = tens.permute(1,2,0).numpy()
    if normalized: 
        img = img*std + mean
    if img.shape[2] == 1:
        img = img.squeeze()
    img = (img + abs(np.amin(img))) / (abs(np.amin(img))+abs(np.amax(img)))
    return img

def visualizationOutGray(data, output, target, classes, normalized):
    '''
    Used to show the first test image in a batch with its label and prediction
    Data size is batch_size, 1, 28, 28 (grayscale images!)
    '''
    ig = plt.figure()
    output_cpu = output.to(torch.device("cpu"))
    target_cpu = target.to(torch.device("cpu"))
    output_idx = (np.argmax(output_cpu[0], axis=0)) #reverse one hot
    cls = classes[output_idx]
    plt.title("Prediction = " + str(cls) + " | Actual = " + str(classes[target_cpu[0].numpy()]) )
    data_cpu = data.to(torch.device("cpu"))
    img = unnormTensor(data_cpu[0], normalized)
    plt.imshow(img, cmap = 'gray')
    plt.pause(0.05)

def plot_confusion_matrix(y_true, y_pred, classes,
                          normalize=False,
                          title=None,
                          cmap=plt.cm.Blues):
    
    y_true = np.array(y_true).astype(int).reshape(-1)
    y_pred = np.array(y_pred).astype(int).reshape(-1)

    #COMBINE LABELS
    '''
    y_true[y_true == 0] = 1 #combine PCT
    y_pred[y_pred == 0] = 1
    
    y_true[y_true == 10] = 5 #combine cd45 and the subclasses
    y_pred[y_pred == 10] = 5
    y_true[y_true == 11] = 5 
    y_pred[y_pred == 11] = 5
    y_true[y_true == 12] = 5 
    y_pred[y_pred == 12] = 5
    y_true[y_true == 9] = 5 
    y_pred[y_pred == 9] = 5
    '''

     
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """


    # Compute confusion matrix
    cm2 = confusion_matrix(y_true, y_pred)
    cm = cm2#[:-1,:-1] #remove CNT
    row_sum_list = []
    accs = []
    for i,row in enumerate(cm):
        if np.sum(row) > 0:
            accs.append(cm[i,i] / np.sum(row))
        row_sum_list.append(np.sum(row))
    print("Accuracy:", accs)
    balanced_accuracy = np.mean(accs)
    print("balanced accuracy:", balanced_accuracy)
    balanced_accuracy_adjust = np.trace(cm) / np.sum(cm)
    balanced_accuracy_adjust = balanced_accuracy
    print('Balanced Accuracy adjust= {:.4f}'.format(balanced_accuracy_adjust))
    
    # Only use the labels that appear in the data
    class_list = []
    #print(unique_labels(y_true, y_pred))
    #print(classes[0])
    for item in unique_labels(y_true, y_pred): class_list.append(classes[item])
    classes = class_list
    
    row_total_counts = dict(zip(classes, row_sum_list))
    accs =[ '%.2f' % elem for elem in accs ]
    accuracy_per_cell = dict(zip(classes, accs))
    print("\nRow wise total counts:") 
    pprint(row_total_counts)
    print("\nAccuracy for each biological cell:") 
    pprint(accuracy_per_cell)
        
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("\nNormalized confusion matrix")
    else:
        print('\nConfusion matrix, without normalization')

    if not title:
        if normalize:
            title = 'Normalized confusion matrix'
        else:
            title = 'Average Recall = {:.2f}%'.format(balanced_accuracy_adjust*100)
    print(cm)

    fig, ax = plt.subplots()
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    # We want to show all ticks...
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           # ... and label them with the respective list entries
           xticklabels=classes, yticklabels=classes,
           title=title,
           ylabel='True label',
           xlabel='Predicted label')
    ax.set_ylim(len(classes)-.5, -.5)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    fmt = '.2f' if normalize else 'd'
    #print("cm.max():", cm.max())
    try:
        if (cm.max() > 0):
            thresh = cm.max() / 2
    except ValueError:  #raised if 'cm.max()' is empty.
        pass

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    plt.show()
    return ax
