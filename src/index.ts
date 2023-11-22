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

// 
const kernels_specs = [
  {
    name: 'xlite',
    dir: 'xlite',
    display_name: 'xlite',
    language: 'python',
    argv: [],
    resources: {
      'logo-32x32': logo32,
      'logo-64x64': logo64
    }
  }
];


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
