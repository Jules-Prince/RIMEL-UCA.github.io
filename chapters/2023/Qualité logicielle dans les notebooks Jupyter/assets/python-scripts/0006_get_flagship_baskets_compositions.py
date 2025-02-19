#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from gs_quant.markets.indices_utils import get_flagships_constituents
from gs_quant.session import Environment, GsSession

# In[ ]:


client = 'CLIENT ID'
secret = 'CLIENT SECRET'

GsSession.use(Environment.PROD, client_id=client, client_secret=secret, scopes=('read_product_data',))

# In[ ]:


get_flagships_constituents()
