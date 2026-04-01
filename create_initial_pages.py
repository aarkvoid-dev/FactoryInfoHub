#!/usr/bin/env python3
"""
Script to create initial pages for the website.
Run this script after migrating the database.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/Users/arfatulshaikh/Projects/InfoHub/FactoryInfoHub')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
django.setup()

from Home.models import Page, PageSection

def create_initial_pages():
    """Create initial pages with content."""
    
    # Create Terms and Conditions page
    terms_page, created = Page.objects.get_or_create(
        slug='terms-and-conditions',
        defaults={
            'title': 'Terms and Conditions',
            'page_type': 'terms',
            'content': '<p>These terms and conditions outline the rules and regulations for the use of FactoryInfoHub\'s Website.</p>',
            'meta_title': 'Terms and Conditions - FactoryInfoHub',
            'meta_description': 'Read our terms and conditions for using FactoryInfoHub services.',
            'is_published': True
        }
    )
    
    if created:
        # Add sections to Terms page
        PageSection.objects.create(
            page=terms_page,
            title='Introduction',
            content='<p>Welcome to FactoryInfoHub! These terms and conditions govern your use of our website. We offer you the ability to browse and search for factory information.</p>',
            order=1
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Intellectual Property Rights',
            content='<p>Other than the content you own, under these Terms, FactoryInfoHub and/or its licensors own all the intellectual property rights and materials contained in this Website.</p><p>You are granted limited license only for purposes of viewing the material contained on this Website.</p>',
            order=2
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Restrictions',
            content='<p>You are specifically restricted from all of the following:</p><ul><li>publishing any Website material in any other media;</li><li>selling, sublicensing and/or otherwise commercializing any Website material;</li><li>publicly performing and/or showing any Website material;</li><li>using this Website in any way that is or may be damaging to this Website;</li><li>using this Website in any way that impacts user access to this Website;</li><li>using this Website contrary to applicable laws and regulations, or in any way may cause harm to the Website, or to any person or business entity;</li><li>engaging in any data mining, data harvesting, data extracting or any other similar activity in relation to this Website;</li><li>using this Website to engage in any advertising or marketing.</li></ul>',
            order=3
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Your Content',
            content='<p>In these Website Standard Terms and Conditions, "Your Content" shall mean any audio, video text, images or other material you choose to display on this Website. By displaying Your Content, you grant FactoryInfoHub a non-exclusive, worldwide irrevocable, sub licensable license to use, reproduce, adapt, publish, translate and distribute it in any and all media.</p><p>Your Content must be your own and must not be invading any third-party’s rights. FactoryInfoHub reserves the right to remove any of Your Content from this Website at any time without notice.</p>',
            order=4
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='No warranties',
            content='<p>This Website is provided "as is," with all faults, and FactoryInfoHub express no representations or warranties, of any kind related to this Website or the materials contained on this Website. Also, nothing contained on this Website shall be interpreted as advising you.</p>',
            order=5
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Limitation of liability',
            content='<p>In no event shall FactoryInfoHub, nor any of its officers, directors and employees, shall be held liable for anything arising out of or in any way connected with your use of this Website whether such liability is under contract.  FactoryInfoHub, including its officers, directors and employees shall not be held liable for any indirect, consequential or special liability arising out of or in any way related to your use of this Website.</p>',
            order=6
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Indemnification',
            content='<p>You hereby indemnify to the fullest extent FactoryInfoHub from and against any and/or all liabilities, costs, demands, causes of action, damages and expenses arising in any way related to your breach of any of the provisions of these Terms.</p>',
            order=7
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Severability',
            content='<p>If any provision of these Terms is found to be invalid under any applicable law, such provisions shall be deleted without affecting the remaining provisions herein.</p>',
            order=8
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Variation of Terms',
            content='<p>FactoryInfoHub is permitted to revise these Terms at any time as it sees fit, and by using this Website you are expected to review these Terms on a regular basis.</p>',
            order=9
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Assignment',
            content='<p>The FactoryInfoHub is allowed to assign, transfer, and subcontract its rights and/or obligations under these Terms without any notification. However, you are not allowed to assign, transfer, or subcontract any of your rights and/or obligations under these Terms.</p>',
            order=10
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Entire Agreement',
            content='<p>These Terms constitute the entire agreement between FactoryInfoHub and you in relation to your use of this Website, and supersede all prior agreements and understandings.</p>',
            order=11
        )
        
        PageSection.objects.create(
            page=terms_page,
            title='Governing Law & Jurisdiction',
            content='<p>These Terms will be governed by and interpreted in accordance with the laws of the State of in, and you submit to the non-exclusive jurisdiction of the state and federal courts located in in for the resolution of any disputes.</p>',
            order=12
        )
        
        print(f"Created Terms and Conditions page with {terms_page.sections.count()} sections")
    else:
        print("Terms and Conditions page already exists")

    # Create Privacy Policy page
    privacy_page, created = Page.objects.get_or_create(
        slug='privacy-policy',
        defaults={
            'title': 'Privacy Policy',
            'page_type': 'privacy',
            'content': '<p>Your privacy is important to us. It is FactoryInfoHub\'s policy to respect your privacy regarding any information we may collect from you through our website.</p>',
            'meta_title': 'Privacy Policy - FactoryInfoHub',
            'meta_description': 'Read our privacy policy to understand how we collect and use your information.',
            'is_published': True
        }
    )
    
    if created:
        # Add sections to Privacy page
        PageSection.objects.create(
            page=privacy_page,
            title='Information We Collect',
            content='<p>We collect several different types of information for various purposes to provide and improve our service to you.</p><p><strong>Personal Data</strong></p><p>While using our Service, we may ask you to provide us with certain personally identifiable information that can be used to contact or identify you ("Personal Data"). Personally identifiable information may include, but is not limited to:</p><ul><li>Email address</li><li>First name and last name</li><li>Phone number</li><li>Address, State, Province, ZIP/Postal code, City</li><li>Cookies and Usage Data</li></ul><p><strong>Usage Data</strong></p><p>We may also collect information on how the Service is accessed and used ("Usage Data"). This Usage Data may include information such as your computer\'s Internet Protocol address (e.g. IP address), browser type, browser version, the pages of our Service that you visit, the time and date of your visit, the time spent on those pages, unique device identifiers and other diagnostic data.</p>',
            order=1
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Tracking & Cookies Data',
            content='<p>We use cookies and similar tracking technologies to track the activity on our Service and hold certain information.</p><p>Cookies are files with small amount of data which may include an anonymous unique identifier. Cookies are sent to your browser from a website and stored on your device. Tracking technologies also used are beacons, tags, and scripts to collect and track information and to improve and analyze our Service.</p><p>You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent. However, if you do not accept cookies, you may not be able to use some portions of our Service.</p><p>Examples of Cookies we use:</p><ul><li><strong>Session Cookies.</strong> We use Session Cookies to operate our Service.</li><li><strong>Preference Cookies.</strong> We use Preference Cookies to remember your preferences and various settings.</li><li><strong>Security Cookies.</strong> We use Security Cookies for security purposes.</li></ul>',
            order=2
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Use of Data',
            content='<p>FactoryInfoHub uses the collected data for various purposes:</p><ul><li>To provide and maintain the Service</li><li>To notify you about changes to our Service</li><li>To allow you to participate in interactive features of our Service when you choose to do so</li><li>To provide customer care and support</li><li>To provide analysis or valuable information so that we can improve the Service</li><li>To monitor the usage of the Service</li><li>To detect, prevent and address technical issues</li></ul>',
            order=3
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Transfer Of Data',
            content='<p>Your information, including Personal Data, may be transferred to — and maintained on — computers located outside of your state, province, country or other governmental jurisdiction where the data protection laws may differ than those from your jurisdiction.</p><p>If you are located outside and choose to provide information to us, please note that we transfer the data, including Personal Data, to and process it there.</p><p>Your consent to this Privacy Policy followed by your submission of such information represents your agreement to that transfer.</p><p>FactoryInfoHub will take all steps reasonably necessary to ensure that your data is treated securely and in accordance with this Privacy Policy and no transfer of your Personal Data will take place to an organization or a country unless there are adequate controls in place including the security of your data and other personal information.</p>',
            order=4
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Disclosure Of Data',
            content='<p><strong>Legal Requirements</strong></p><p>FactoryInfoHub may disclose your Personal Data in the good faith belief that such action is necessary to:</p><ul><li>To comply with a legal obligation</li><li>To protect and defend the rights or property of FactoryInfoHub</li><li>To prevent or investigate possible wrongdoing in connection with the Service</li><li>To protect the personal safety of users of the Service or the public</li><li>To protect against legal liability</li></ul>',
            order=5
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Security Of Data',
            content='<p>The security of your data is important to us, but remember that no method of transmission over the Internet, or method of electronic storage is 100% secure. While we strive to use commercially acceptable means to protect your Personal Data, we cannot guarantee its absolute security.</p>',
            order=6
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Service Providers',
            content='<p>We may employ third party companies and individuals to facilitate our Service ("Service Providers"), to provide the Service on our behalf, to perform Service-related services or to assist us in analyzing how our Service is used.</p><p>These third parties have access to your Personal Data only to perform these tasks on our behalf and are obligated not to disclose or use it for any other purpose.</p>',
            order=7
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Links To Other Sites',
            content='<p>Our Service may contain links to other sites that are not operated by us. If you click on a third party link, you will be directed to that third party\'s site. We strongly advise you to review the Privacy Policy of every site you visit.</p><p>We have no control over and assume no responsibility for the content, privacy policies or practices of any third party sites or services.</p>',
            order=8
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Children\'s Privacy',
            content='<p>Our Service does not address anyone under the age of 18 ("Children").</p><p>We do not knowingly collect personally identifiable information from anyone under the age of 18. If you are a parent or guardian and you are aware that your Children has provided us with Personal Data, please contact us. If we become aware that we have collected Personal Data from children without verification of parental consent, we take steps to remove that information from our servers.</p>',
            order=9
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Changes To This Privacy Policy',
            content='<p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page.</p><p>We will let you know via email and/or a prominent notice on our Service, prior to the change becoming effective and update the "effective date" at the top of this Privacy Policy.</p><p>You are advised to review this Privacy Policy periodically for any changes. Changes to this Privacy Policy are effective when they are posted on this page.</p>',
            order=10
        )
        
        PageSection.objects.create(
            page=privacy_page,
            title='Contact Us',
            content='<p>If you have any questions about this Privacy Policy, please contact us:</p><ul><li>By email: info@factoryinfohub.com</li><li>By visiting this page on our website: <a href="/contact">Contact Us</a></li></ul>',
            order=11
        )
        
        print(f"Created Privacy Policy page with {privacy_page.sections.count()} sections")
    else:
        print("Privacy Policy page already exists")

    # Create Disclaimer page
    disclaimer_page, created = Page.objects.get_or_create(
        slug='disclaimer',
        defaults={
            'title': 'Disclaimer',
            'page_type': 'disclaimer',
            'content': '<p>This disclaimer governs your use of FactoryInfoHub\'s website. Please read this disclaimer carefully before using our website.</p>',
            'meta_title': 'Disclaimer - FactoryInfoHub',
            'meta_description': 'Read our disclaimer to understand the limitations of our service.',
            'is_published': True
        }
    )
    
    if created:
        # Add sections to Disclaimer page
        PageSection.objects.create(
            page=disclaimer_page,
            title='General Disclaimer',
            content='<p>The information contained on this website is for general information purposes only. The information is provided by FactoryInfoHub and while we endeavor to keep the information up to date and correct, we make no representations or warranties of any kind, express or implied, about the completeness, accuracy, reliability, suitability or availability with respect to the website or the information, products, services, or related graphics contained on the website for any purpose. Any reliance you place on such information is therefore strictly at your own risk.</p>',
            order=1
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='External Links Disclaimer',
            content='<p>Through this website you are able to link to other websites which are not under the control of FactoryInfoHub. We have no control over the nature, content and availability of those sites. The inclusion of any links does not necessarily imply a recommendation or endorse the views expressed within them.</p>',
            order=2
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='Accuracy of Information',
            content='<p>While we strive to provide accurate and up-to-date information about factories, we cannot guarantee the accuracy, completeness, or reliability of all information on this website. Factory information may change without notice, and some details may be outdated or incorrect.</p><p>We recommend that you verify any critical information with the factory directly or through other reliable sources before making any decisions based on the information provided on this website.</p>',
            order=3
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='No Professional Advice',
            content='<p>The content on this website is provided for informational purposes only and should not be considered as professional advice. We are not liable for any losses, injuries, or damages from the display or use of this information or from decisions you make based on information found on this website.</p>',
            order=4
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='Limitation of Liability',
            content='<p>In no event shall FactoryInfoHub be liable for any direct, indirect, incidental, special, consequential or exemplary damages, including but not limited to, damages for loss of profits, goodwill, use, data or other intangible losses resulting from the use of or inability to use this website.</p>',
            order=5
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='User Responsibility',
            content='<p>By using this website, you agree that you are responsible for your own safety and well-being when visiting any factory listed on this website. You agree to follow all safety protocols and guidelines provided by the factory and to take all necessary precautions to ensure your safety.</p>',
            order=6
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='Intellectual Property',
            content='<p>All content on this website, including text, images, graphics, and other materials, is the property of FactoryInfoHub or its content suppliers and is protected by intellectual property laws. You may not reproduce, distribute, modify, or create derivative works of any content on this website without our express written permission.</p>',
            order=7
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='Changes to This Disclaimer',
            content='<p>We reserve the right to update or change this disclaimer at any time without prior notice. Your continued use of the website following the posting of changes to this disclaimer will be considered your acceptance of those changes.</p>',
            order=8
        )
        
        PageSection.objects.create(
            page=disclaimer_page,
            title='Governing Law',
            content='<p>This disclaimer shall be governed and construed in accordance with the laws of the jurisdiction in which FactoryInfoHub operates, without regard to its conflict of law provisions.</p>',
            order=9
        )
        
        print(f"Created Disclaimer page with {disclaimer_page.sections.count()} sections")
    else:
        print("Disclaimer page already exists")

    print("\nAll initial pages have been created successfully!")
    print(f"Total pages created: {Page.objects.count()}")

if __name__ == "__main__":
    create_initial_pages()