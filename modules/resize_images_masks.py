import math
import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
from utils import DataReader

class ImageResizer :
    '''
        This class enables us to resized an original mask and its corresponding 
        satellite image into smaller square masks and images.
    '''
    def __init__(self, images_dir : str, masks_dir : str,resized_images_dir : str,
                 resized_masks_dir : str, image_size : int) :

        self.images_dir = images_dir
        self.masks_dir = masks_dir
        self.resized_images_dir = resized_images_dir
        self.resized_masks_dir = resized_masks_dir
        # the size of the new squared images and masks
        self.image_size = image_size
        # Dictionary that will contain the infos of the smaller squared masks of identical size
        self.smaller_masks = {'values':[], 'coordinates':[]}
        # Dictionary that will contain the infos of the best masks
        self.dict_best_masks = {'values':[], 'coordinates':[]}
        self.number_width_height = ()
        

    def cutting_mask(self, image_name, show = False):
        '''
        This function cuts the original mask into smaller masks of size 512x512 (by default). 
        The objective is to cover the entire original mask with smaller masks of the same size
        while reducing as much as possible the intersection area between them.
        '''
        data_reader = DataReader()
        og_mask = data_reader.read_mask(os.path.join(self.masks_dir, image_name)
                             .replace('.png', '_mask.png'))
        height, width = og_mask.shape
        
        # Definiton of the number of images along the height of the original mask
        # height = len(og_mask[:,0])
        number_height_images = math.ceil(height/self.image_size)
        height_shift = (((number_height_images * self.image_size) - height)/ \
                        (number_height_images-1))
        
        # Definiton of the number of images along the width of the original mask
        # width = len(og_mask[0,:])
        number_width_images = math.ceil(width/self.image_size)
        width_shift = (((number_width_images * self.image_size) - width)/ (number_width_images-1))
        
        # Definition of the list that contains the smaller masks of identical size
        self.smaller_masks = {'values':[], 'coordinates':[]}
        for height_idx in range(number_height_images) :
            for width_idx in range(number_width_images) :
                start_point_height = int((height_idx * self.image_size) - \
                                         (height_shift * height_idx))
                start_point_width = int((width_idx * self.image_size) - \
                                        (width_shift * width_idx))
                
                self.smaller_masks['values'].append(og_mask[start_point_height:start_point_height+self.image_size,
                                                    start_point_width:start_point_width+self.image_size])
                self.smaller_masks['coordinates'].append((start_point_height,start_point_width))
        
        # Find the smaller mask that as the largest amout of parking spot 
        size_of_parking = [sum(sum(self.smaller_masks.get('values')[i])) for i in range(len(self.smaller_masks.get('values')))]
        max_parking_mask = np.argmax(size_of_parking)
        
        # Save the number of masks on the width and on the height insed the dictionnary. Useful for later visual verifications with plt.
        self.number_width_height = (number_height_images, number_width_images)
        
        # Display the smaller masks to check that everything is correct    
        if show :
            _ , axs = plt.subplots(number_height_images, number_width_images, figsize=(8,8))
            for ax, mask, idx in zip(axs.ravel(), self.smaller_masks.get('values'),
                                     range(len(size_of_parking))):
                ax.imshow(mask)
                # Highlight the smaller mask with the largest parking spot in red
                if idx == max_parking_mask :
                    ax.spines['bottom'].set_color('red')
                    ax.spines['top'].set_color('red')
                    ax.spines['right'].set_color('red')
                    ax.spines['left'].set_color('red')
                    ax.tick_params(left = False,
                                   right = False,
                                   labelleft = False ,
                                   labelbottom = False,
                                   bottom = False)
                else :
                    ax.axis('off')
            plt.tight_layout()
            plt.show()
            
        return self.smaller_masks  
    
    def best_masks(self, number_of_mask : int, show = False): 
        '''
            This function takes a list of smaller masks and return the "number_of_mask"
            masks with the largets area considered as a parking spot. 
        '''
        
        list_of_parking_size = [sum(sum(self.smaller_masks.get('values')[i])) for i in range(len(self.smaller_masks.get('values')))]
        
        # Initialisation of the dictionary containning the best masks. 
        self.dict_best_masks = {'values':[], 'coordinates':[]}
        
        for _ in range(number_of_mask) :
            max_mask_idx = np.argmax(list_of_parking_size)
            self.dict_best_masks['values'].append(self.smaller_masks.get('values')[max_mask_idx])
            self.dict_best_masks['coordinates'].append(self.smaller_masks.get('coordinates')[max_mask_idx])
            # Remove the max that has been added to the dictionary 
            list_of_parking_size[max_mask_idx] = -1
            
        # Display the best masks to check that everything is correct
        if show :
            _, axs = plt.subplots(self.number_width_height[0],
                                    self.number_width_height[1], 
                                    figsize=(8,8))
            
            for ax, mask, parking_size in zip(axs.ravel(), self.smaller_masks.get('values'), list_of_parking_size):
                
                # Show only the best masks 
                if parking_size == -1 :
                    ax.imshow(mask)
            
                ax.axis('off')
                
            plt.tight_layout()
            plt.show()
        
        return self.dict_best_masks
    
    def save_new_images_masks(self, number_of_mask, image_name : str, show = False):
        """
        blabla
        """
    
        # Create smaller masks
        self.cutting_mask(image_name)
       
        # Select the masks that contains the largest area of parking spot
        self.best_masks(number_of_mask)

        # Retrieve the original image
        og_image = cv2.imread(os.path.join(self.images_dir, image_name))

        for mask_idx in range(len(self.dict_best_masks.get('coordinates'))) : 

            # Get the top/right coordinates of the new smaller mask
            y_starting_point, x_starting_point = self.dict_best_masks.get('coordinates')[mask_idx]

            # Recreate the new square smaller corresponding image from those coordinates
            new_image = og_image[y_starting_point:y_starting_point+self.image_size, 
                               x_starting_point:x_starting_point+self.image_size,
                               :]

            # Save the new smaller mask 
            resized_mask_path = os.path.join(self.resized_masks_dir, image_name).replace('.png', f'_{mask_idx+1}_mask.png')
            directory_manager.ensure_directory_exists(resized_mask_path)
            cv2.imwrite(resized_mask_path,
                      self.dict_best_masks.get('values')[mask_idx])

            # Save the new corresponding image
            resized_image_path = os.path.join(self.resized_images_dir, image_name).replace('.png', f'_{mask_idx+1}.png')
            directory_manager.ensure_directory_exists(resized_image_path)
            cv2.imwrite(resized_image_path,
                      new_image)

        print(f'{image_name} correctly resized into {len(self.dict_best_masks.get("coordinates"))}',
              f'square images of size {self.image_size}px')

        # Display the image to check that everything is correct 
        if show :  
            plt.imshow(og_image[:,:,::-1])
            plt.axis('off')
