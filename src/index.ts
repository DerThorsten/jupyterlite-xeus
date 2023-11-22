// Copyright (c) Thorsten Beier
// Copyright (c) JupyterLite Contributors
// Distributed under the terms of the Modified BSD License.

import {
  IServiceWorkerManager,
  JupyterLiteServer,
  JupyterLiteServerPlugin
} from '@jupyterlite/server';
import { IBroadcastChannelWrapper } from '@jupyterlite/contents';
import { IKernel, IKernelSpecs } from '@jupyterlite/kernel';

import { WebWorkerKernel } from './web_worker_kernel';

import logo32 from '!!file-loader?context=.!../style/logos/python-logo-32x32.png';
import logo64 from '!!file-loader?context=.!../style/logos/python-logo-64x64.png';


const xhr = new XMLHttpRequest();
const json_url = '../extensions/@jupyterlite/xeus-python-kernel/static/xlite/kernels.json'
xhr.open("GET", json_url, false);
xhr.send(null);
const kernel_names = JSON.parse(xhr.responseText);
console.log(kernel_names);

// create kernelspecs from kernels.json

function name2lang(name) {
  if (name == "xlite") {
    return "bash";
  } else if (name == "xlua") {
    return "lua";
  } else {
    return "unknown";
  }
}


const kernels_specs = kernel_names.map((kernel_name) => {
  let spec = {
    name: kernel_name,
    dir: kernel_name,
    display_name: kernel_name,
    language: name2lang(kernel_name),
    argv: [],
    resources: {
      'logo-32x32': logo32,
      'logo-64x64': logo64
    }
  }
  return spec;
});


const server_kernels = kernels_specs.map((spec) => {
  let server_kernel : JupyterLiteServerPlugin<void> = {
    // use name from spec
    id: `@jupyterlite/${spec.name}-extension:kernel`, 
    autoStart: true,
    requires: [IKernelSpecs],
    optional: [IServiceWorkerManager, IBroadcastChannelWrapper],
    activate: (
      app: JupyterLiteServer,
      kernelspecs: IKernelSpecs,
      serviceWorker?: IServiceWorkerManager,
      broadcastChannel?: IBroadcastChannelWrapper
    ) => {
      kernelspecs.register({
        spec: spec,
        create: async (options: IKernel.IOptions): Promise<IKernel> => {
          const mountDrive = !!(
            serviceWorker?.enabled && broadcastChannel?.enabled
          );
  
          if (mountDrive) {
            console.info(
              'xeus-python contents will be synced with Jupyter Contents'
            );
          } else {
            console.warn(
              'xeus-python contents will NOT be synced with Jupyter Contents'
            );
          }
  
          return new WebWorkerKernel({
            ...options,
            mountDrive
          },
          spec
          );
        }
      });
    }
  };
  return server_kernel;
});




const plugins: JupyterLiteServerPlugin<any>[] = server_kernels;

export default plugins;
