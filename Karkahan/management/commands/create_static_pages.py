from django.core.management.base import BaseCommand
from Home.models import Page
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Create static pages (About Us, Refund Policy) in the database'

    def handle(self, *args, **options):
        # About Us page
        about_content = """
<section class="layout-pt-xl layout-pb-xl bg-gradient-primary">
  <div class="container">
    <div data-anim="slide-up" class="row justify-center">
      <div class="col-xl-8 col-lg-9 col-md-10">
        <div class="text-center">
          <div class="d-inline-flex items-center px-20 py-8 rounded-full bg-white-10 text-white fw-600 text-14 mb-25 backdrop-blur">
            <i class="fas fa-info-circle mr-10"></i> ABOUT
          </div>
          <h1 class="text-54 fw-800 text-white tracking-tighter mb-20">About <span class="text-accent-1">Fashion Chemistry</span></h1>
          <p class="text-18 text-white opacity-80 max-w-600 mx-auto">Connecting fashion professionals worldwide through reliable information.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="layout-pt-md layout-pb-xl bg-light-1">
  <div class="container">
    <div class="row justify-center">
      <div class="col-lg-10">
        <div class="bg-white rounded-24 px-45 py-50 md:px-25 md:py-30 shadow-xl border-light">
          
          <div class="row y-gap-40">
            <div class="col-12">
              <p class="text-17 text-dark-3 leading-lg">Fashion Chemistry is a fashion industry information platform dedicated to connecting fashion designers, brand owners, exporters, and manufacturers. Our goal is simple — to help fashion professionals connect more easily and build successful business relationships.</p>
            </div>

            <div class="col-md-4 text-center">
              <div class="size-80 rounded-full bg-accent-1-10 d-flex items-center justify-center mx-auto mb-15">
                <i class="icon-flag text-40 text-accent-1"></i>
              </div>
              <h4 class="text-18 fw-600">Our Mission</h4>
              <p class="text-14 text-light-1 mt-5">Bridge the information gap in fashion manufacturing</p>
            </div>

            <div class="col-md-4 text-center">
              <div class="size-80 rounded-full bg-accent-1-10 d-flex items-center justify-center mx-auto mb-15">
                <i class="icon-eye text-40 text-accent-1"></i>
              </div>
              <h4 class="text-18 fw-600">Our Vision</h4>
              <p class="text-14 text-light-1 mt-5">A globally connected fashion community</p>
            </div>

            <div class="col-md-4 text-center">
              <div class="size-80 rounded-full bg-accent-1-10 d-flex items-center justify-center mx-auto mb-15">
                <i class="icon-heart text-40 text-accent-1"></i>
              </div>
              <h4 class="text-18 fw-600">Our Commitment</h4>
              <p class="text-14 text-light-1 mt-5">Accurate, reliable, up-to-date information</p>
            </div>

            <div class="col-12">
              <div class="bg-accent-1-05 rounded-12 p-30 mt-20">
                <div class="d-flex">
                  <i class="icon-bulb text-30 text-accent-1 mr-20"></i>
                  <div>
                    <h5 class="text-16 fw-600">Core Purpose</h5>
                    <p class="text-15 text-dark-3 mt-5">We bridge the information gap in the fashion manufacturing industry, making it easier for businesses to find reliable partners and suppliers.</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="col-12">
              <hr class="border-light my-30">
              <div class="row y-gap-20">
                <div class="col-md-6">
                  <h5 class="fw-600 mb-10">📍 Contact Person</h5>
                  <p>IZHAR</p>
                </div>
                <div class="col-md-6">
                  <h5 class="fw-600 mb-10">📧 Email</h5>
                  <p>infofashionchemistry@gmail.com</p>
                </div>
                <div class="col-md-6">
                  <h5 class="fw-600 mb-10">📞 Phone</h5>
                  <p>+91 9022116040</p>
                </div>
                <div class="col-md-6">
                  <h5 class="fw-600 mb-10">🏭 Founded</h5>
                  <p>2026</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</section>
"""

        try:
            about_page = Page.objects.all_with_deleted().get(page_type='about')
            if about_page.is_deleted:
                # Restore the soft-deleted page
                about_page.restore()
                self.stdout.write(
                    self.style.SUCCESS('Successfully restored About Us page')
                )
            # Update the page content regardless
            about_page.title = 'About Us'
            about_page.slug = 'about-us'
            about_page.content = about_content
            about_page.meta_title = 'About Us - Fashion Chemistry'
            about_page.meta_description = 'Learn about Fashion Chemistry and our mission to connect fashion professionals worldwide.'
            about_page.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully updated About Us page')
            )
        except Page.DoesNotExist:
            # Create new page
            about_page = Page.objects.create(
                page_type='about',
                title='About Us',
                slug='about-us',
                content=about_content,
                meta_title='About Us - Fashion Chemistry',
                meta_description='Learn about Fashion Chemistry and our mission to connect fashion professionals worldwide.',
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created About Us page')
            )

        # Refund Policy page
        refund_content = """
<section class="layout-pt-xl layout-pb-xl bg-gradient-primary">
  <div class="container">
    <div data-anim="slide-up" class="row justify-center">
      <div class="col-xl-8 col-lg-9 col-md-10">
        <div class="text-center">
          <div class="d-inline-flex items-center px-20 py-8 rounded-full bg-white-10 text-white fw-600 text-14 mb-25 backdrop-blur">
            <i class="fas fa-undo-alt mr-10"></i> REFUND POLICY
          </div>
          <h1 class="text-54 fw-800 text-white tracking-tighter mb-20">Refund <span class="text-accent-1">Policy</span></h1>
          <p class="text-18 text-white opacity-80 max-w-600 mx-auto">Understanding our refund process for digital information services.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="layout-pt-md layout-pb-xl bg-light-1">
  <div class="container">
    <div class="row justify-center">
      <div class="col-lg-10">
        <div class="bg-white rounded-24 px-45 py-50 md:px-25 md:py-30 shadow-xl border-light">
          
          <div class="policy-section">
            <h2 class="text-22 fw-700 mb-20">Digital Information Service</h2>
            <p class="text-15 text-dark-3 leading-lg">Because our services are digital in nature (access to Establishment contact details, listing information, and industry insights), all sales are generally final. Once you have accessed the information, the service is considered delivered.</p>
          </div>

          <div class="policy-section">
            <h2 class="text-22 fw-700 mb-20">Non‑Refundable</h2>
            <p class="text-15 text-dark-3 leading-lg">Payments made for access to contact details or any digital content are non‑refundable, as per the nature of the product. We do not guarantee business outcomes, and no refunds will be issued for lack of expected results.</p>
          </div>

          <div class="policy-section">
            <h2 class="text-22 fw-700 mb-20">Exceptions</h2>
            <p class="text-15 text-dark-3 leading-lg">In the rare case of a duplicate payment or a technical error that prevents you from accessing the purchased information, please contact us within 48 hours. We will review the issue and may issue a refund or credit at our discretion.</p>
          </div>

          <div class="policy-section">
            <h2 class="text-22 fw-700 mb-20">How to Request a Review</h2>
            <p class="text-15 text-dark-3 leading-lg">If you believe you are eligible for a refund due to a technical issue, please email us at <strong>infofashionchemistry@gmail.com</strong> with your payment details and a description of the problem. We will respond within 3 business days.</p>
          </div>

          <div class="bg-accent-1-05 rounded-12 p-30 mt-20">
            <div class="d-flex">
              <i class="icon-help-circle text-30 text-accent-1 mr-20"></i>
              <div>
                <h5 class="text-16 fw-600">Need Help?</h5>
                <p class="text-15 text-dark-3 mt-5">If you have any questions about our refund policy, please contact our support team at infofashionchemistry@gmail.com or call +91 9022116040.</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</section>
"""

        try:
            refund_page = Page.objects.all_with_deleted().get(page_type='refund')
            if refund_page.is_deleted:
                # Restore the soft-deleted page
                refund_page.restore()
                self.stdout.write(
                    self.style.SUCCESS('Successfully restored Refund Policy page')
                )
            # Update the page content regardless
            refund_page.title = 'Refund Policy'
            refund_page.slug = 'refund-policy'
            refund_page.content = refund_content
            refund_page.meta_title = 'Refund Policy - Fashion Chemistry'
            refund_page.meta_description = 'Learn about our refund policy for digital information services.'
            refund_page.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully updated Refund Policy page')
            )
        except Page.DoesNotExist:
            # Create new page
            refund_page = Page.objects.create(
                page_type='refund',
                title='Refund Policy',
                slug='refund-policy',
                content=refund_content,
                meta_title='Refund Policy - Fashion Chemistry',
                meta_description='Learn about our refund policy for digital information services.',
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created Refund Policy page')
            )

        self.stdout.write(
            self.style.SUCCESS('Static pages creation completed!')
        )