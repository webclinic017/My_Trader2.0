#!/usr/bin/env python
# coding: utf-8

# In[7]:


from my_libs import *


# In[8]:


with open("/home/ken/notebook/My_Trader2.0/record-Copy1.txt") as file:
    my_p = file.readline()
    my_p = file.readline()
    my_p = file.readline()


# In[9]:


robinhood = get_robinhood()


# In[10]:


robinhood.login("lgyhz1234@gmail.com", my_p)


hedge = robinhood.hedge_addup()


# In[6]:


my_beta_min = robinhood.get_my_position_beta_minute()


# In[ ]:


html = my_beta_min.style.set_table_attributes('border="1" class="dataframe table table-hover table-bordered"')

html = html.render()

html += "<br><br>" + hedge

send_email(html, title = "Minute_Beta")

