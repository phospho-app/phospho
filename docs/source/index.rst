Welcome to phospho!
===================

.. figure:: ./assets/phospho-logo.png
  :align: center
  :alt: phospho
  :class: no-scaled-link
  :width: 50%
  

.. raw:: html

   <p style="text-align:center">
   <strong>The LLM apps analytics platform
   </strong>
   </p>

   <p style="text-align:center">
   <script src="https://code.iconify.design/3/3.1.0/iconify.min.js"></script>
   <a href="https://github.com/phospho-app/phospho" aria-label="Github"><span class="iconify" data-icon="mdi:github"></span> Github</a>
   <a href="mailto:contact@phospho.app" aria-label="Contact us"><span class="iconify" data-icon="material-symbols:mail"></span> Contact us</a>
   <a href="https://discord.gg/Pu4Hf9UAJC" aria-label="Discord"><span class="iconify" data-icon="ic:baseline-discord"></span> Discord</a>
   
   </p>

.. _phospho: https://phospho-portal-git-alpha-phospho-team.vercel.app/


`phospho`_ is a platform to monitor what your users are talking about on your LLM app.

* Catch technical issues before your users do
* Measure performance to quickly improve your product
* Understand what users *actually* want to do and which version of your product is the most successful

Getting started
===============

You can get started with phospho in minutes.

#. Create an account on `phospho`_. No credit card required to get started.
#. Install the `Python SDK <https://pypi.org/project/phospho/>`_, or directly use the HTTP API. 
#. Start logging. Get analyses of your user interactions in the phospho dashboard.

.. code-block:: python

   import phospho
   import openai

   phospho.init(api_key="get your key on phospho.app", project_id="same")
   openai_client = openai.OpenAI(api_key="openai-key")

   # This is your agent code
   query = {
      "messages": [{"role": "user", "content": "Say this is a test"}], 
      "model": "gpt-3.5-turbo", 
   }
   response = openai_client.chat.completions.create(**query)

   # --> This is how you log stuff to phospho
   phospho.log(input=query, output=response)


See `Getting Started </getting_started/quickstart.html>`_ for detailed instructions.

Get in touch
------------

We are a team of AI builders that want to enable observability for LLM-apps at scale. 

Feel free to reach out to *contact@phospho.app* for technical questions, job opportunities, and any other inquiry.

We are also on `Discord <https://discord.gg/wk4uBSnKyW>`_. Come and chat with the community!


Documentation
-------------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   getting_started/quickstart

.. toctree::
   :maxdepth: 1
   :caption: FAQ

   faq/faq


