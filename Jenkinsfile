#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {  
    label {
      label "system_tests_ioc"
    }
  }
  
  triggers {
    pollSCM('H/2 * * * *')
    cron('H H/4 * * *')
  }
  
  stages {  
    stage("Checkout") {
      steps {
        checkout scm
      }
    }

    stage("Install latest IBEX") {
      steps {
        bat """
            echo "Done in the job Install client, server and genie_python"
            """
      }
    }
    
    stage("System Tests") {
      steps {
        bat """
            call "C:\Instrument\Apps\EPICS\support\IocTestFramework\master\run_all_tests.bat"
            """
        junit "test-reports/**/*.xml"
      }
    }
  }
  
  post {
    failure {
      step([$class: 'Mailer', notifyEveryUnstableBuild: true, recipients: 'icp-buildserver@lists.isis.rl.ac.uk', sendToIndividuals: true])
    }
  }
  
  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'5', daysToKeepStr: '7'))
    timeout(time: 300, unit: 'MINUTES')
    disableConcurrentBuilds()
  }
}
