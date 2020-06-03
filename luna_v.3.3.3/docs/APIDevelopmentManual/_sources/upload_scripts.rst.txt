.. _upload-scripts:

Upload scripts
==============


We realized  several scripts uploading images to LUNA API. All these scripts you can found in folder *uploads_scripts*.

Use cases:

    1) We have folder with images. We want send these images to LUNA API  to extract descriptors and attach
       the resulting descriptors to list of descriptors.

    #) We have folder with images. We want send these images to LUNA API  to extract descriptors, create person
       for each the resulting  descriptor and attach persons to list of persons.

    #) We have several folders with images in one folder. We want create persons for each folders, extract descriptors
       from images from folders and attach descriptors to corresponding persons. Optionally  we should be can attach
       persons to a list of persons.

For first two case you can use *upload_folder_to_list_objects.py*.

Command-line arguments of script:

--help        print help for using command-line arguments
--src         folder with images
--dst         destination, address of lina python service, default *"http://127.0.0.1:5000"*
--lg          login from LUNA API account
--psw         password from LUNA API account
--list        account list, if it does not set list will be created
--obj         type of creating object, 'person' or 'descriptor'
--smf         skip images with several faces, default False
--c           concurrency, count simultaneously processing images, default 1, type int
--warped      all images is warped
--sud         use file name as user_data. only when obj is person, default False

Example of run.

.. code-block:: bash

    python upload_folder_to_list_objects.py --src="/test/imgs" --c=10 --dst="http://127.0.0.1:5001"\
     --lg=hornsandhooves@ya.ru --psw=secretpassword --list=418592e3-fc69-4901-9fc0-3f9865462814 --smf --sud --obj=person

For third case you can use *upload_folders_with_person.py*.

Command-line arguments of script:

--help        print help for using command-line arguments
--src         folder with person folders
--dst         destination, address of lina python service, default *"http://127.0.0.1:5000"*
--lg          login from LUNA API account
--psw         password from LUNA API account
--wList       does not attach persons to list, default False
--list        persons list of account, if  it does not set and wList does not set, list will be created
--mdp         max descriptors on 1 person, -1 - all, default -1
--c           concurrency, count simultaneously processing images, default 1, type int
--warped      all images is warped
--sud         use file name as user_data. only when obj is person, default False

If several faces was detected image would be skiped.

Example of run.

.. code-block:: bash

    python upload_folders_with_person.py --src="/test/persons" --c=10 --dst="http://127.0.0.1:5001"\
     --lg=hornsandhooves@ya.ru --psw=secretpassword --list=418592e3-fc69-4901-9fc0-3f9865462814 --warped --sud

Both scripts create  2 logs files. First file contains with errors that occurred during the program, second
file contains info about creating object in LUNA API.

