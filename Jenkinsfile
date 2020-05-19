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
            set ERRCODE=%ERRORLEVEL%
            rmdir /s /q ibex_utils
            if %ERRCODE% NEQ 0 EXIT /B 1
            """
      }
    }
    
    stage("System Tests") {
      steps {
        bat """
            del /q C:\\Instrument\\Var\\logs\\IOCTestFramework\\*.*
            call "C:\\Instrument\\Apps\\EPICS\\support\\IocTestFramework\\master\\run_all_tests.bat"
            """
      }
    }
  }
  
  post {
    always {
      bat """
          robocopy "C:\\Instrument\\Var\\logs\\IOCTestFramework" "%WORKSPACE%\\test-logs" /E /PURGE /R:2 /MT /NFL /NDL /NP /NC /NS /LOG:NUL
      """
      archiveArtifacts artifacts: 'test-logs/*.log', caseSensitive: false
      junit "test-reports/**/*.xml"
    }
  }
}
