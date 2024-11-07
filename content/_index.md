---
# Leave the homepage title empty to use the site title
title: ""
date: 2024-11-07
type: landing

design:
  # Default section spacing
  spacing: "6rem"

sections:
  - block: resume-biography-3
    content:
      # Choose a user profile to display (a folder name within `content/authors/`)
      username: admin
      text: ""
      # Show a call-to-action button under your biography? (optional)
      button:
        text: Download CV
        url: uploads/JMH_CV.pdf
    design:
      css_class: dark
      background:
        color: black
        image:
          # Add your image background to `assets/media/`.
          filename: JADES_GS_z14_0_Small.jpg
          filters:
            brightness: 1.0
          size: cover
          position: center
          parallax: false
  - block: markdown
    content:
      title: 'My Research'
      subtitle: ''
      text: |-
        When, how, and why did the first stars, galaxies, and galaxy clusters form? In what ways did large-scale structure influence these first structures? And what sources of radiation reionized the Universe? These questions, which drive modern extragalactic astronomy, are core to my research. Using data from the James Webb Space Telescope (JWST), I have worked to: (#1) identify, characterize, and understand galaxies and galaxy clusters in the very early Universe; while (#2) connecting the physical properties of the most distant known galaxies and galaxy clusters with their large-scale environment. In particular, I have made numerous and impactful contributions toward the selection, photometric redshift determination, physical property inference, and interpretation of galaxies and galaxy clusters at the redshift frontier. I have extensive experience interpreting observations from three out of the four instruments on JWST: the Mid-Infrared Instrument (MIRI), the Near Infrared Camera (NIRCam), and the Near Infrared Spectrograph (NIRSpec), with a specific emphasis in the wide field slitless spectroscopic (WFSS) observing mode of NIRCam. My contributions to extragalactic astronomy have been featured in national and international press, and I have worked to share my work and acquired knowledge with the broader community.
        I believe that sharing knowledge with others, which in turn educates and inspires the future generations of humanity and scientists, is one of the most important and significant activities that we can do as astronomers. To this end, I have spent my time mentoring, teaching, and tutoring local undergraduate students in mathematics and science at both the introductory and advanced level. While an undergraduate student, I co-organized a weekly extragalactic seminar at Princeton University. During graduate school, I co-organized a bi-weekly extragalactic seminar at the University of Arizona, which included lectures and workshops related to using JWST and understanding the high-redshift Universe. I recently started educating amateur astronomers and high school students in Tucson, AZ about JWST. Furthermore, my research related to my help discovering and understanding the most distant known galaxy, JADES-GS-z14-0, has been featured in national and international press, including <a href="https://blogs.nasa.gov/webb/2024/05/30/nasas-james-webb-space-telescope-finds-most-distant-known-galaxy/">a blog post from NASA</a> that already has more than one million impressions, and <a href="https://www.youtube.com/watch?v=FR7VGHauNxw">an interview filmed by the University of Arizona</a>.
    design:
      columns: '1'
  - block: collection
    id: papers
    content:
      title: First-Author Publications
      filters:
        folders:
          - publication
        featured_only: true
    design:
      view: article-grid
      columns: 2
  - block: collection
    content:
      title: Complete List of Publications
      text: ""
      filters:
        folders:
          - publication
        exclude_featured: false
    design:
      view: citation
#   - block: collection
#     id: talks
#     content:
#       title: Recent & Upcoming Talks
#       filters:
#         folders:
#           - event
#     design:
#       view: article-grid
#       columns: 1
#   - block: collection
#     id: news
#     content:
#       title: Recent News
#       subtitle: ''
#       text: ''
#       # Page type to display. E.g. post, talk, publication...
#       page_type: post
#       # Choose how many pages you would like to display (0 = all pages)
#       count: 5
#       # Filter on criteria
#       filters:
#         author: ""
#         category: ""
#         tag: ""
#         exclude_featured: false
#         exclude_future: false
#         exclude_past: false
#         publication_type: ""
#       # Choose how many pages you would like to offset by
#       offset: 0
#       # Page order: descending (desc) or ascending (asc) date.
#       order: desc
#     design:
#       # Choose a layout view
#       view: date-title-summary
#       # Reduce spacing
#       spacing:
#         padding: [0, 0, 0, 0]
  - block: cta-card
    demo: true # Only display this section in the Hugo Blox Builder demo site
    content:
      title: 👉 Build your own academic website like this
      text: |-
        This site is generated by Hugo Blox Builder - the FREE, Hugo-based open source website builder trusted by 250,000+ academics like you.

        <a class="github-button" href="https://github.com/HugoBlox/hugo-blox-builder" data-color-scheme="no-preference: light; light: light; dark: dark;" data-icon="octicon-star" data-size="large" data-show-count="true" aria-label="Star HugoBlox/hugo-blox-builder on GitHub">Star</a>

        Easily build anything with blocks - no-code required!
        
        From landing pages, second brains, and courses to academic resumés, conferences, and tech blogs.
      button:
        text: Get Started
        url: https://hugoblox.com/templates/
    design:
      card:
        # Card background color (CSS class)
        css_class: "bg-primary-700"
        css_style: ""
---
