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

  environment {
    NODE = "${env.NODE_NAME}"
    ELOCK = "epics_${NODE}"
  }

  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'7', daysToKeepStr: '7'))
    timestamps()
    // as we "checkout scm" as a stage, we do not need to do it here too
    skipDefaultCheckout(true)
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
    throttleJobProperty(
          categories: ['system_tests_ioc'],
          throttleEnabled: true,
          throttleOption: 'category'
    )
  }

  stages {  
    stage("Checkout") {
      steps {
        retry(3) {
            echo "Branch: ${env.BRANCH_NAME}"
            checkout scm
        }
      }
    }

    stage("Install latest IBEX") {
      steps {
         lock(resource: ELOCK, inversePrecedence: false) {
           bat """
            if EXIST "ibex_utils" rmdir /s /q ibex_utils
            git clone https://github.com/ISISComputingGroup/ibex_utils.git ibex_utils
            set \"MYJOB=${env.JOB_NAME}\"
            REM EPICS should always be a directory junction on build servers
            if exist "C:\\Instrument\\Apps\\EPICS" (
                call "C:\\Instrument\\Apps\\EPICS\\stop_ibex_server.bat"
                rmdir "C:\\Instrument\\Apps\\EPICS"
            )
            if \"%MYJOB%\" == \"System_Tests_IOCs_debug\" (
                call ibex_utils/installation_and_upgrade/instrument_install_latest_build_only.bat CLEAN EPICS_DEBUG
            ) else (
                call ibex_utils/installation_and_upgrade/instrument_install_latest_build_only.bat
            )
            set INSTERR=%ERRORLEVEL%
            rmdir /s /q ibex_utils
            if exist "C:\\Instrument\\Apps\\EPICS-%MYJOB%" (
                REM Retry delete multiple times as sometimes fails
                rd /q /s C:\\Instrument\\Apps\\EPICS-%MYJOB%>NUL
                rd /q /s C:\\Instrument\\Apps\\EPICS-%MYJOB%>NUL
                rd /q /s C:\\Instrument\\Apps\\EPICS-%MYJOB%>NUL
            )
            move C:\\Instrument\\Apps\\EPICS C:\\Instrument\\Apps\\EPICS-%MYJOB%
            set MOVEERR=%ERRORLEVEL%
            IF %INSTERR% NEQ 0 (
                @echo ERROR: unable to install ibex
                exit /b %INSTERR%
            )
            IF %MOVEERR% NEQ 0 (
                @echo ERROR: unable to rename directory
                exit /b %MOVEERR%
            )
            """
         }
      }
    }
    
    stage("IOC Tests") {
      steps {
         lock(resource: ELOCK, inversePrecedence: false) {
           timeout(time: 1800, unit: 'MINUTES') {
           bat """
             setlocal EnableDelayedExpansion
             set \"MYJOB=${env.JOB_NAME}\"
             if exist "C:\\Instrument\\Apps\\EPICS" (
                call "C:\\Instrument\\Apps\\EPICS\\stop_ibex_server.bat"
                rmdir "C:\\Instrument\\Apps\\EPICS"
             )
             mklink /J C:\\Instrument\\Apps\\EPICS C:\\Instrument\\Apps\\EPICS-%MYJOB%
             IF %errorlevel% NEQ 0 (
                @echo ERROR: unable to make directory junction
                exit /b %errorlevel%
             )
             if not exist "C:\\Instrument\\Apps\\EPICS\\config_env.bat" (
                @echo ERROR: Unable to find config_env.bat in linked directory
                exit /b 1
             )
             del /q C:\\Instrument\\Var\\logs\\IOCTestFramework\\*.*
             call "C:\\Instrument\\Apps\\EPICS\\support\\IocTestFramework\\master\\run_all_tests_split.bat"
             set ERRCODE=!ERRORLEVEL!
             call "C:\\Instrument\\Apps\\EPICS\\stop_ibex_server.bat"
             rmdir "C:\\Instrument\\Apps\\EPICS"
             exit /b !ERRCODE!
             """
           }
         }
      }
    }
  }
  
  post {
    always {
      bat """
          robocopy "C:\\Instrument\\Var\\logs\\IOCTestFramework" "%WORKSPACE%\\test-logs" /E /R:2 /MT /NFL /NDL /NP /NC /NS /LOG:NUL
          exit /b 0
      """
      archiveArtifacts artifacts: 'test-logs/*.log', caseSensitive: false
      junit "test-reports/**/*.xml"
    }

    cleanup {
      bat """
        set \"MYJOB=${env.JOB_NAME}\"
        REM not ideal to call without lock, and retaking lock may be a potential race condition
        REM however the directory junction will only exist if the previous step times out      
        if exist "C:\\Instrument\\Apps\\EPICS" (
            call "C:\\Instrument\\Apps\\EPICS-%MYJOB%\\stop_ibex_server.bat"
        )
        rmdir /s /q "C:\\Instrument\\Apps\\EPICS-%MYJOB%"
        exit /b 0
      """
    }
  }

}
