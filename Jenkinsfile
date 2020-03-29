#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {  
    label {
      label "system_tests_ioc"
    }
  }

  parameters {
      string(name: 'BUILD_PREFIX', defaultValue: 'EPICS', description: 'Build prefix')
      string(name: 'BUILD_SUFFIX', defaultValue: 'CLEAN', description: 'Build suffix')
  }

  triggers {
    pollSCM('H/2 * * * *')
    cron('H H/4 * * *')
  }

  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'5', daysToKeepStr: '7'))
    timeout(time: 600, unit: 'MINUTES')
    disableConcurrentBuilds()
    timestamps()
    office365ConnectorWebhooks([[
                    name: "Office 365",
                    notifyBackToNormal: true,
                    startNotification: false,
                    notifyFailure: true,
                    notifySuccess: false,
                    notifyNotBuilt: false,
                    notifyAborted: false,
                    notifyRepeatedFailure: true,
                    notifyUnstable: true,
                    url: "${env.MSTEAMS_URL}"
            ]]
    )
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
            if EXIST "ibex_utils" rmdir /s /q ibex_utils
            git clone https://github.com/ISISComputingGroup/ibex_utils.git ibex_utils
            set \"MYJOB=${env.JOB_NAME}\"
            call ibex_utils/installation_and_upgrade/instrument_install_latest_build_only.bat \"${params.BUILD_SUFFIX}\" \"${params.BUILD_PREFIX}\"
            rmdir /s /q ibex_utils
            """
      }
    }
    
    stage("System Tests") {
      steps {
        bat """
            call "C:\\Instrument\\Apps\\EPICS\\support\\IocTestFramework\\master\\run_all_tests.bat"
            """
      }
    }
  }
  
  post {
    always {
      junit "test-reports/**/*.xml"
    }
  }
}
