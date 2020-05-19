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

  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'7', daysToKeepStr: '7'))
    timeout(time: 900, unit: 'MINUTES')
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
            if \"%MYJOB%\" == \"System_Tests_IOCs_debug\" (
                call ibex_utils/installation_and_upgrade/instrument_install_latest_build_only.bat CLEAN EPICS_DEBUG
            ) else (
                call ibex_utils/installation_and_upgrade/instrument_install_latest_build_only.bat
            )
            if %ERRORLEVEL% NEQ 0 EXIT /B 1
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
      archiveArtifacts artifacts: 'c:/Instrument/Var/logs/IOCTestFramework/*.log', caseSensitive: false
      junit "test-reports/**/*.xml"
    }
  }
}
