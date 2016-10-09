# KOALA Cloud Manager

KOALA (Karlsruhe Open Application (for) cLoud Administration) is a software service, designed to help you working with your [http://aws.amazon.com](Amazon Web Services) (AWS) compatible cloud services and infrastructures (IaaS). The public cloud services from Amazon and the HP Cloud (that offering is now defunct!) are support as well as private cloud services based on [https://github.com/eucalyptus/eucalyptus](Eucalyptus), [https://github.com/nimbusproject/nimbus](Nimbus) or [https://github.com/OpenNebula/one](OpenNebula). The storage services [https://cloud.google.com/storage/](Google Cloud Storage), [https://www.dunkel.de/s3](Dunkel Cloud Storage) and Host Europe Cloud Storage (that offering is now defunct!) can be used with KOALA too

KOALA helps interacting with cloud services that implement the APIs of 

- [http://aws.amazon.com/ec2/](Elastic Compute Cloud) (EC2) 
- [http://aws.amazon.com/s3/](Simple Storage Service) (S3)
- [http://aws.amazon.com/ebs/](Elastic Block Store) (EBS) 
- [http://aws.amazon.com/elasticloadbalancing/](Elastic Load Balancing) (ELB)

With KOALA the users can start, stop and monitor their instances, volumes and elastic IP addresses. They can also create and erase buckets inside the S3-compatible storage services S3, Google Storage and Walrus. It's easy to upload, check and modify data that is stored inside these storage services, the same way it can be done with [http://www.s3fox.net](S3Fox) and the [https://sandbox.google.com/storage/](Google Storage Manager).

KOALA itself is a service that is able to run inside the public cloud platform (PaaS) [http://appengine.google.com](Google App Engine) and inside Private Cloud platforms with [https://github.com/AppScale/appscale](AppScale) or [http://code.google.com/p/typhoonae/](typhoonAE).

**A customized version for Android and iPhone/iPod touch devices is included.**

# Publications

- **The KOALA Cloud Manager - Cloud Service Management the Easy Way**. *Christian Baun, Marcel Kunze, Viktor Mauch*. Proceedings of the IEEE Cloud 2011 4th International Conference on Cloud Computing in Washington. ISBN:978-0-7695-4460-1
- **The KOALA Cloud Management Service - A Modern Approach for Cloud Infrastructure Management**. *Christian Baun, Marcel Kunze*. Proceedings of the 1st International Workshop on Cloud Computing Platforms (CloudCP) that was part of the EuroSys 2011 in Salzburg. The Association for Computing Machinery (ACM). ISBN:978-1-4503-0727-7

# How do I get started?

The Wiki tab provides instructions on how to use KOALA that runs as a service inside the Google App Engine with the most popular Cloud Services and how to install KOALA inside a Private Cloud PaaS.

Web site of KOALA: [http://koalacloud.appspot.com](http://koalacloud.appspot.com)

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/S8pGPm-vSTk/0.jpg)](http://www.youtube.com/watch?v=S8pGPm-vSTk)

# Reason for the Development and Design Decisions

All existing tools to work with cloud services face several advantages and drawbacks.

- Online tools (software services) like the [http://aws.amazon.com/console/](AWS Management Console) and the [https://console.cloud.google.com](Google Cloud Console) are in line with just the cloud service offerings of the company. It is currently not foreseen to configure it in a way to e.g. work with services from an Eucalyptus private cloud infrastructure. [http://www.ylastic.com](Ylastic) offers support for most AWS cloud services and Eucalyptus infrastructures but it is not possible to work with other compatible infrastructures e.g. Nimbus. As the access keys are stored with the provider, the customer also has to trust the provider of the management tool regarding privacy and availability.
- Firefox browser extensions like [https://sourceforge.net/projects/elasticfox/](ElasticFox),[[http://code.google.com/p/hybridfox/](Hybridfox) and [http://www.s3fox.net](S3Fox) only work with the Firefox browser and not e.g. Internet Explorer, Opera, Google Chrome or Safari. The customers have to install and maintain the management tool on their local computer, a fact that somehow does not reflect the cloud paradigm very well.
- Command-line tools like the AWS tools offered by Amazon only support the AWS public cloud offerings. The [https://github.com/eucalyptus/euca2ools](Euca2ools) from the Eucalyptus project and [https://cloud.google.com/storage/docs/gsutil](GSUtil) from Google support both, public and private cloud services. They require a local installation and lack ease of use as they implement no graphical user interface (GUI).
- Locally installed applications with a GUI like [http://www.elasticwolf.com](ElasticWolf), [https://github.com/neillturner/ec2dream](EC2Dream), [http://www.gladinet.com](Gladinet Cloud Desktop) and [https://cyberduck.io](Cyberduck) provide a better level of usability compared to command-line tools but not all applications run with every operating system and they require a local installation.

In order to improve the situation, KOALA has been developed as a flexible and open solution to satisfy all needs for the daily work with cloud services that comply to the AWS API.
